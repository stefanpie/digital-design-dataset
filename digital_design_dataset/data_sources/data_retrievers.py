import base64
import io
import json
import re
import shutil
import subprocess
import tarfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

import py7zr
import requests
from github import Github
from github.ContentFile import ContentFile

from digital_design_dataset.data_sources.github_fast_downloader import GithubFastDownloader
from digital_design_dataset.design_dataset import (
    SOURCE_FILES_EXTENSIONS_SET,
    DesignDataset,
    build_design_scaffolding,
)
from digital_design_dataset.utils import auto_find_bin


def get_file_from_github(
    gh_api: Github,
    owner: str,
    repo: str,
    path: str,
    timeout: int | None = None,
) -> str:
    repo_ = gh_api.get_repo(f"{owner}/{repo}")
    data = repo_.get_contents(path)
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(f"Expected 1 file, found {len(data)}")
        data = data[0]

    content = data.content
    if not content:
        download_url = data.download_url
        r = requests.get(download_url, timeout=timeout)
        # if r.status_code != requests.status_codes.codes.ok:
        if r.status_code != requests.codes.ok:
            raise RuntimeError(
                f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
            )
        return r.content.decode("utf-8")
    return base64.b64decode(content).decode("utf-8")


def get_file_from_github_binary(
    gh_api: Github,
    owner: str,
    repo: str,
    path: str,
    timeout: int | None = None,
) -> bytes:
    repo_ = gh_api.get_repo(f"{owner}/{repo}")
    data = repo_.get_contents(path)
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(f"Expected 1 file, found {len(data)}")
        data = data[0]

    download_url = data.download_url
    r = requests.get(download_url, timeout=timeout)
    # if r.status_code != requests.status_codes.codes.ok:
    if r.status_code != requests.codes.ok:
        raise RuntimeError(
            f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
        )
    assert isinstance(r.content, bytes)
    return r.content


def get_file_download_url_from_github(
    gh_api: Github,
    owner: str,
    repo: str,
    path: str,
) -> str:
    repo_ = gh_api.get_repo(f"{owner}/{repo}")
    data = repo_.get_contents(path)
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(f"Expected 1 file, found {len(data)}")
        data = data[0]

    return data.download_url


def get_listing_from_github(
    gh_api: Github,
    owner: str,
    repo: str,
    path: str,
) -> list[ContentFile]:
    repo_ = gh_api.get_repo(f"{owner}/{repo}")
    listing = repo_.get_contents(path)
    listing = listing if isinstance(listing, list) else [listing]
    return listing


class DataRetriever(ABC):
    dataset_name: str
    dataset_tags: ClassVar[list[str]]

    def __init__(self, design_dataset: DesignDataset) -> None:
        self.design_dataset = design_dataset

    @abstractmethod
    def get_dataset(self, overwrite: bool = False) -> None: ...

    def remove_dataset(self) -> None:
        designs = [d for d in self.design_dataset.index if d["dataset_name"] == self.dataset_name]
        for design in designs:
            design_dir = self.design_dataset.designs_dir / design["design_name"]
            if design_dir.exists():
                shutil.rmtree(design_dir)


class OpencoresDatasetRetriever(DataRetriever):
    dataset_name: str = "opencores"
    dataset_tags: ClassVar[list[str]] = ["open_source"]

    BLACKLIST: ClassVar = [
        "6809_6309_compatible_core",
    ]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(
            "hardware-design-dataset-opencores",
            "stefanpie",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/designs.tar.gz"])
        tar_fp = gfd.get_path_on_disk("designs.tar.gz")

        tar = tarfile.open(tar_fp, mode="r:gz")

        designs = []
        for member in tar.getmembers():
            # get only top level folders "designs/*/"
            # folders may be nested, so we need to check if the folder
            # is a top level folder
            if member.isdir() and member.name.count("/") == 1:
                designs.append(member.name)

        for fn in designs:
            base_name = fn.split("/")[1]
            if base_name in self.BLACKLIST:
                continue
            design_name = f"opencores__{base_name}"
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {
                "design_name": design_name,
                "dataset_name": self.dataset_name,
                "dataset_tags": self.dataset_tags,
            }
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            aux_files_dir = design_dir / "aux_files"
            aux_files_dir.mkdir(parents=True, exist_ok=True)

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            for member in tar.getmembers():
                if member.isfile() and member.name.startswith(f"designs/{base_name}/"):
                    file_name = member.name.split("/")[-1]
                    extension = file_name.split(".")[-1]
                    file_buffer = tar.extractfile(member)
                    if file_buffer is None:
                        raise ValueError(f"Failed to extract file {file_name}")
                    file_content = file_buffer.read().decode("utf-8")
                    if file_name == "top.txt":
                        fp = design_dir / "top.txt"
                        fp.write_text(file_content)
                    if f".{extension}" in SOURCE_FILES_EXTENSIONS_SET:
                        fp = source_file_dir / file_name
                        fp.write_text(file_content)
                    else:
                        fp = aux_files_dir / file_name
                        fp.write_text(file_content)

        # Close the tar file
        tar.close()
        gfd.cleanup()


class HW2VecDatasetRetriever(DataRetriever):
    dataset_name: str = "hw_2_vec"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    BLACKLIST = "RS232-T100"

    def get_dataset(self, overwrite: bool = False, timeout: int = 30) -> None:
        gfd = GithubFastDownloader(
            "hw2vec",
            "AICPS",
        )

        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/assets/datasets.zip"])
        zip_fp = gfd.get_path_on_disk("assets/datasets.zip")

        z = zipfile.ZipFile(zip_fp)

        designs = []
        for fn in z.namelist():
            if fn[-2:] == ".v":
                designs.append(fn)

        for fn in designs:
            base_name = fn.split("/")[-2]
            design_name = f"hw2vec__{base_name.replace('-', '_')}"

            if base_name in self.BLACKLIST:
                continue
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = source_file_dir / fn.split("/")[-1]
            design_fp.write_text(z.read(fn).decode("utf-8"))

        z.close()
        gfd.cleanup()


class VTRDatasetRetriever(DataRetriever):
    dataset_name: str = "vtr"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    BLACKLIST = (
        "LU8PEEng",
        "LU32PEEng",
        "LU64PEEng",
        "boundtop",
        "mcml",
    )
    # these designs cause issues with yosys auto-expanding memories
    # leading to long runtime and out-of-memory issues
    # TODO: find workaround in the future

    def get_dataset(self, overwrite: bool = True) -> None:
        gfd = GithubFastDownloader(
            "vtr-verilog-to-routing",
            "verilog-to-routing",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()

        gfd.checkout_stuff(["/vtr_flow/benchmarks/verilog", "/vtr_flow/primitives.v"])

        dir_on_disk = gfd.get_path_on_disk("vtr_flow/benchmarks/verilog")
        listing = sorted(dir_on_disk.iterdir())

        file_list: list[tuple[str, Path]] = []
        for content_file in listing:
            if content_file.is_file() and (content_file.suffix == ".v"):
                file_list.append((content_file.name, content_file))

        primitives_file_fp = gfd.get_path_on_disk("vtr_flow/primitives.v")
        primitives_file_txt = primitives_file_fp.read_text()

        primitives_file_txt = primitives_file_txt.replace(
            "module single_port_ram",
            "(* nomem2reg *)\nmodule single_port_ram",
        )
        primitives_file_txt = primitives_file_txt.replace(
            "module dual_port_ram",
            "(* nomem2reg *)\nmodule dual_port_ram",
        )
        primitives_file_txt = primitives_file_txt.replace(
            "reg [DATA_WIDTH-1:0] Mem[MEM_DEPTH-1:0];",
            "(* nomem2reg *) reg [DATA_WIDTH-1:0] Mem[MEM_DEPTH-1:0];",
        )

        for file in file_list:
            base_name = file[0].replace(".v", "")
            design_name = f"vtr__{base_name}"
            if base_name in self.BLACKLIST:
                continue
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = source_file_dir / file[0]
            shutil.copy(file[1], design_fp)

            design_primitives_fp = source_file_dir / "primitives.v"
            design_primitives_fp.write_text(primitives_file_txt)

        gfd.cleanup()


class KoiosDatasetRetriever(DataRetriever):
    dataset_name: str = "koios"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(
            "vtr-verilog-to-routing",
            "verilog-to-routing",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/vtr_flow/benchmarks/verilog/koios"])

        dir_on_disk = gfd.get_path_on_disk("vtr_flow/benchmarks/verilog/koios")
        listing = sorted(dir_on_disk.iterdir())

        file_list: list[tuple[str, Path]] = []
        for content_file in listing:
            if content_file.is_file() and (content_file.suffix == ".v"):
                file_list.append((content_file.name, content_file))

        file_list = list(filter(lambda x: "_include.v" not in x[0], file_list))

        for file in file_list:
            base_name = file[0].replace(".v", "")
            design_name = f"koios__{base_name}"
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = source_file_dir / file[0]
            shutil.copy(file[1], design_fp)

        gfd.cleanup()


class EPFLDatasetRetriever(DataRetriever):
    dataset_name: str = "epfl"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(
            "benchmarks",
            "lsils",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/arithmetic", "/random_control"])

        dir_on_disk_arithmetic = gfd.get_path_on_disk("arithmetic")
        listing_arithmetic = sorted(dir_on_disk_arithmetic.iterdir())

        dir_on_disk_random_control = gfd.get_path_on_disk("random_control")
        listing_random_control = sorted(dir_on_disk_random_control.iterdir())

        listing = listing_arithmetic + listing_random_control

        file_list: list[dict[str, str | Path]] = []
        for content_file in listing:
            if content_file.is_file() and (content_file.suffix == ".v"):
                file_list.append({
                    "name": content_file.name,
                    "path": content_file.relative_to(gfd.repo_dir),
                    "path_on_disk": content_file,
                })

        for file in file_list:
            if not isinstance(file["name"], str):
                raise TypeError(f"Expected str, got {type(file['name'])}")
            base_name = file["name"].replace(".v", "")
            design_name = f"epfl__{base_name}"
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            if not isinstance(file["path_on_disk"], Path):
                raise TypeError(f"Expected Path, got {type(file['path_on_disk'])}")
            design_fp = source_file_dir / file["name"]
            shutil.copy(file["path_on_disk"], design_fp)

        gfd.cleanup()


class OPDBDatasetRetriever(DataRetriever):
    dataset_name: str = "opdb"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(
            "OPDB",
            "PrincetonUniversity",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/modules/piton_baseline_designs.txt"])

        design_list_fp = gfd.get_path_on_disk("modules/piton_baseline_designs.txt")
        design_list = design_list_fp.read_text()

        new_gh_paths = design_list.splitlines()
        new_gh_paths = [p for p in new_gh_paths if p.strip()]

        gfd.checkout_stuff(new_gh_paths, reset=False)

        for design in design_list.splitlines():
            base_name = "_".join(design.split("/")[1:]).replace(".v", "").replace(".pickle", "")
            design_name = f"opdb__{base_name}"
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = gfd.get_path_on_disk(design)
            shutil.copy(design_fp, source_file_dir / (base_name + ".v"))

        gfd.cleanup()


class ISCAS85DatasetRetriever(DataRetriever):
    dataset_name: str = "iscas85"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    ISCAS_85_89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/ISCAS.7z"

    def get_dataset(self, overwrite: bool = False, timeout: int = 30) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "iscas.7z"
        with (
            requests.get(self.ISCAS_85_89_URL, stream=True, timeout=timeout) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"Verilog/c.*?\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            isca85_verilog_files = [n for n in archive.getnames() if filter_pattern.match(n)]

            for file_name in isca85_verilog_files:
                case_name = file_name.split("/")[-1].replace(".v", "")
                case_name = case_name.upper()
                design_name = f"iscas85__{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "Verilog")


class ISCAS89DatasetRetriever(DataRetriever):
    dataset_name: str = "iscas89"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    ISCAS_85_89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/ISCAS.7z"

    def get_dataset(self, overwrite: bool = False, timeout: int = 30) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "iscas.7z"

        with (
            requests.get(self.ISCAS_85_89_URL, stream=True, timeout=timeout) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            extra_files = ["Verilog/lib.v", "Verilog/DFF2.v"]
            for file_name in extra_files:
                archive.extract(targets=[file_name], path=temp_dir_fp)
                archive.reset()

        filter_pattern = re.compile(r"Verilog/s.*?\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            isca85_verilog_files = [n for n in archive.getnames() if filter_pattern.match(n)]

            for file_name in isca85_verilog_files:
                case_name = file_name.split("/")[-1].replace(".v", "")
                case_name = case_name.upper()
                design_name = f"iscas89__{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "Verilog")

                shutil.copy(temp_dir_fp / "Verilog" / "lib.v", source_file_dir)
                shutil.copy(temp_dir_fp / "Verilog" / "DFF2.v", source_file_dir)


class LGSynth89DatasetRetriever(DataRetriever):
    dataset_name: str = "lgsynth89"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    LGSYNTH89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/LGSynth89.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "lgsynth89.7z"
        with (
            requests.get(self.LGSYNTH89_URL, stream=True, timeout=10) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"LGSynth89/Verilog/.*?_orig\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            verilog_files = [n for n in archive.getnames() if filter_pattern.match(n)]

            for file_name in verilog_files:
                case_name = file_name.split("/")[-1].replace("_orig.v", "")
                design_name = f"lgsynth89__{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)

                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "LGSynth89")


class LGSynth91DatasetRetriever(DataRetriever):
    dataset_name: str = "lgsynth91"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    LGSYNTH91_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/LGSynth91.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "lgsynth89.7z"
        with (
            requests.get(self.LGSYNTH91_URL, stream=True, timeout=10) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"LGSynth91/Verilog/.*?/.*?_orig\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            verilog_files = [n for n in archive.getnames() if filter_pattern.match(n)]

            for file_name in verilog_files:
                case_name = file_name.split("/")[-1].replace("_orig.v", "").replace(".", "_")
                design_name = f"lgsynth91__{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)

                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "LGSynth91")


RE_BLIF_BROKEN_CONSTANT = re.compile(r"(.names +.*? *\n) *([0,1,-]) *$", re.MULTILINE)


def fix_blif_constant_expr(fp: Path) -> None:
    t = fp.read_text()

    const_exprs = []

    matches = RE_BLIF_BROKEN_CONSTANT.finditer(t)
    for match in matches:
        _whole = match.group(0)
        name_line = match.group(1)
        const = match.group(2)
        name_line = name_line.replace("  ", " ")
        if const == "0":
            new_str = name_line + f"{const}"
        if const == "1":
            new_str = name_line + f"{const}"
        if const == "-":
            new_str = " "
        const_exprs.append(new_str)
        t = t.replace(match.group(0), "")

    lines = t.splitlines()
    # find the ".end" line
    end_line_idx = lines.index(".end")
    # insert the new constant expressions before the ".end" line
    for const_expr in const_exprs:
        lines.insert(end_line_idx, const_expr)

    t = "\n".join(lines)

    fp.write_text(t)


RE_BLIF_MODEL = re.compile(r"\.model +(.+)(:?.|\n)*?\.end", re.MULTILINE)


def fix_blif_duplicate_model_definition(fp: Path) -> None:
    t = fp.read_text()
    models = RE_BLIF_MODEL.finditer(t)
    model_data = [
        (
            match.group(0),
            match.group(1),
        )
        for match in models
    ]
    seen_models = set()
    for model_text, model_name in model_data:
        if model_name in seen_models:
            t = t.replace(model_text, "\n\n", 1)
        else:
            seen_models.add(model_name)

    fp.write_text(t)


class IWLS93DatasetRetriever(DataRetriever):
    dataset_name: str = "iwls93"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    IWLS93_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/IWLS93.7z"

    BLACKLIST: ClassVar = ["diffeq", "elliptic", "frisc", "tseng"]

    def get_dataset(self, overwrite: bool = False) -> None:
        yosys_bin = auto_find_bin("yosys")
        if yosys_bin is None:
            raise RuntimeError(
                "Yosys is needed to preprocess the IWLS93 dataset. "
                "Yosys was not found in PATH or in the "
                "YOSYS_PATH environment variable.",
            )

        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "lgsynth89.7z"
        with (
            requests.get(self.IWLS93_URL, stream=True, timeout=10) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"blif/.*?\.blif")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            blif_files = [n for n in archive.getnames() if filter_pattern.match(n)]

            for file_name in blif_files:
                base_name = file_name.split("/")[-1].replace(".blif", "")

                if base_name in self.BLACKLIST:
                    continue

                design_name = f"iwls93__{base_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources_blif"
                source_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "blif")

                fix_blif_constant_expr(new_fp)
                fix_blif_duplicate_model_definition(new_fp)

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)

                yosys_script = f"""
                read_blif -sop {source_file_dir / new_fp}
                techmap t:$sop
                write_verilog {source_file_dir / base_name}.v
                """

                temp_dir_yosys = TemporaryDirectory()
                temp_dir_fp_yosys = Path(temp_dir_yosys.name)
                temp_script_fp = temp_dir_fp_yosys / "script.ys"
                temp_script_fp.write_text(yosys_script)

                p = subprocess.run(
                    [yosys_bin, "-s", temp_script_fp],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if p.returncode != 0:
                    raise RuntimeError(
                        f"Yosys failed to convert {new_fp} to Verilog:\n{p.stdout}\n{p.stderr}\n",
                    )


class I99TDatasetRetriever(DataRetriever):
    dataset_name: str = "i99t"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    I99T_URL: str = "https://github.com/cad-polito-it/I99T/archive/refs/tags/v2.tar.gz"

    BLACKLIST: ClassVar[list[str]] = [
        "b08",
        "b30",
    ]

    def get_dataset(self, overwrite: bool = False) -> None:
        # check for yosys
        yosys_bin = auto_find_bin("yosys")
        if yosys_bin is None:
            raise RuntimeError(
                "Yosys is needed to preprocess the I99T dataset. "
                "Yosys was not found in PATH or in the "
                "YOSYS_PATH environment variable.",
            )
        p = subprocess.run(
            [yosys_bin, "-m", "ghdl", "-p", ""],
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode != 0:
            raise RuntimeError(
                "Yosys is missing the ghdl module. Please install ghdl to be used with yosys.",
            )

        gfd = GithubFastDownloader(
            "I99T",
            "cad-polito-it",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/i99t"])

        dir_on_disk = gfd.get_path_on_disk("i99t")
        paths_on_disk = sorted([p for p in dir_on_disk.iterdir() if p.is_dir()])
        paths = [str(p.relative_to(gfd.repo_dir)) for p in paths_on_disk]

        for path in paths:
            base_name = path.split("/")[-1]
            if base_name in self.BLACKLIST:
                continue
            design_name = f"i99t_{base_name}"

            vhd_name = f"{base_name}.vhd"
            vhdl_name = f"{base_name}.vhdl"

            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_tags"] = self.dataset_tags
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_vhdl_file_dir = design_dir / "sources_vhdl"
            source_vhdl_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = gfd.get_path_on_disk(f"{path}/{vhd_name}")
            shutil.copy(design_fp, source_vhdl_file_dir / vhdl_name)

            sources_file_dir = design_dir / "sources"
            sources_file_dir.mkdir(parents=True, exist_ok=True)

            yosys_script = f"""
            ghdl --ieee=synopsys --std=08 {source_vhdl_file_dir / vhdl_name} -e {base_name}
            write_verilog {sources_file_dir / base_name}.v
            """

            temp_dir_yosys = TemporaryDirectory()
            temp_dir_fp_yosys = Path(temp_dir_yosys.name)
            temp_script_fp = temp_dir_fp_yosys / "script.ys"
            temp_script_fp.write_text(yosys_script)

            p = subprocess.run(
                [yosys_bin, "-m", "ghdl", "-s", temp_script_fp],
                text=True,
                capture_output=True,
                check=False,
            )
            if p.returncode != 0:
                raise RuntimeError(
                    f"Yosys failed to convert {vhdl_name} to Verilog:\n{p.stdout}\n{p.stderr}\n",
                )

        gfd.cleanup()


class AddersCVUTDatasetRetriever(DataRetriever):
    dataset_name: str = "adders_cvut"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    ADDERS_CVUT_URL: str = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/Adders.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        # check for yosys
        yosys_bin = auto_find_bin("yosys")
        if yosys_bin is None:
            raise RuntimeError(
                "Yosys is needed to preprocess the Adders CVUT dataset. "
                "Yosys was not found in PATH or in the "
                "YOSYS_PATH environment variable.",
            )

        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "adders.7z"
        with (
            requests.get(self.ADDERS_CVUT_URL, stream=True, timeout=10) as r,
            temp_file_fp.open("wb") as f,
        ):
            shutil.copyfileobj(r.raw, f)

        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            files = [p for p in archive.getnames() if p.endswith(".blif") and not p.endswith("_col.blif")]

            for file_name in files:
                base_name = file_name.split("/")[-1].replace(".blif", "").replace("-", "_")
                design_name = f"adders_cvut__{base_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_blif_file_dir = design_dir / "sources_blif"
                source_blif_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[file_name], path=source_blif_file_dir)
                archive.reset()

                current_fp = source_blif_file_dir / Path(file_name)
                new_fp = source_blif_file_dir / Path(file_name).name
                current_fp.rename(new_fp)

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)

                yosys_script = f"""
                read_blif -sop {source_blif_file_dir / new_fp}
                techmap t:$sop
                write_verilog {source_file_dir / base_name}.v
                """

                temp_dir_yosys = TemporaryDirectory()
                temp_dir_fp_yosys = Path(temp_dir_yosys.name)
                temp_script_fp = temp_dir_fp_yosys / "script.ys"
                temp_script_fp.write_text(yosys_script)

                p = subprocess.run(
                    [yosys_bin, "-s", temp_script_fp],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if p.returncode != 0:
                    raise RuntimeError(
                        f"Yosys failed to convert {new_fp} to Verilog:\n{p.stdout}\n{p.stderr}\n",
                    )


RE_CELL_ARRAY_INSTANCE = re.compile(r"[\w\d]+ +(?:#\(.*?\) +)*[\w\d]+\[\d+:\d+\]")


def unroll_cell_array(inst_str: str) -> list[str]:
    inst_str = inst_str.replace("](", "] (")
    parts = inst_str.split(" ")

    # get the cell name
    cell_name = parts.pop(0)
    # check if there are any parameters
    cell_params = None
    if "#" in inst_str:
        cell_params = parts.pop(0)

    # get the instance name and array size
    inst_name_str = parts.pop(0)
    inst_name, inst_size = inst_name_str.split("[")
    inst_size = inst_size[:-1]
    inst_range = [int(x) for x in inst_size.split(":")]

    port_data_all = []
    # get the port list
    port_list = parts.pop(0)
    port_list = port_list.replace("(", "").replace(")", "").replace(";", " ")
    port_list = port_list.split(",")
    port_list = [x.strip() for x in port_list]
    for port in port_list:
        port_name, port_range = port.split("[")
        port_range = port_range[:-1]
        port_range = [int(x) for x in port_range.split(":")]
        port_data_all.append({
            "name": port_name,
            "range": port_range,
        })

    range_size_inst = abs(inst_range[0] - inst_range[1]) + 1
    for port in port_data_all:
        range_size_port = abs(port["range"][0] - port["range"][1]) + 1
        if range_size_port != range_size_inst:
            raise ValueError("Port and instance range sizes do not match")

    inst_dir = 1 if inst_range[0] < inst_range[1] else -1
    inst_vals = list(range(inst_range[0], inst_range[1] + inst_dir, inst_dir))
    port_vals = []
    for port in port_data_all:
        port_dir = 1 if port["range"][0] < port["range"][1] else -1
        port_generator = list(
            range(port["range"][0], port["range"][1] + port_dir, port_dir),
        )
        port_vals.append(port_generator)

    new_cell_lines = []
    for idx in range(range_size_inst):
        line = ""
        line += f"{cell_name} "
        if cell_params is not None:
            line += f"{cell_params} "
        line += f"{inst_name}__{inst_vals[idx]} "
        line += "("
        for port_idx, port in enumerate(port_data_all):
            line += f"{port['name']}[{port_vals[port_idx][idx]}]"
            if port_idx < len(port_data_all) - 1:
                line += ", "
        line += ");"
        new_cell_lines.append(line)

    return new_cell_lines


def unroll_cell_array_instances(fp: Path) -> None:
    t = fp.read_text()
    lines = t.splitlines()
    new_lines = []
    for line in lines:
        if RE_CELL_ARRAY_INSTANCE.match(line):
            unrolled = unroll_cell_array(line)
            new_lines.extend(unrolled)
        else:
            new_lines.append(line)
    t = "\n".join(new_lines)
    fp.write_text(t)


class VerilogAddersMongrelgemDatasetRetriever(DataRetriever):
    dataset_name: str = "verilog_adders_mongrelgem"
    dataset_tags: ClassVar[list[str]] = ["open_source"]

    DATA_URL: str = "https://github.com/mongrelgem/Verilog-Adders"

    DESIGN_FILES: ClassVar[list[str]] = [
        "Carry Lookahead Adder/CarryLookaheadAdder.v",
        "Carry Ripple Adder/CarryRippleAdder.v",
        "Carry Select Adder/CarrySelectAdder.v",
        "Carry Skip Adder/CarrySkipAdder.v",
        "Hybrid Adder/HybridAdder.v",
        "Kogge-Stone Adder/KoggeStoneAdder.v",
    ]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(
            "Verilog-Adders",
            "mongrelgem",
        )
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(self.DESIGN_FILES)

        for design_fp in self.DESIGN_FILES:
            base_name = design_fp.split("/")[-1].replace(".v", "")

            scaffold = build_design_scaffolding(
                self.design_dataset.designs_dir,
                base_name,
                "verilog_adders_mongrelgem",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffold.source_dir

            fp_on_disk = gfd.get_path_on_disk(design_fp)
            text = fp_on_disk.read_text()

            design_fp_local = source_file_dir / design_fp.split("/")[-1]
            design_fp_local.write_text(text)

            unroll_cell_array_instances(design_fp_local)

        gfd.cleanup()


class Texas97DatasetRetriever(DataRetriever):
    dataset_name: str = "texas97"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    DATA_URL: str = "https://ptolemy.berkeley.edu/projects/embedded/research/vis/texas97-benchmarks.tar.gz"

    # TODO: Implement this, requires manual extraction for each design, not too hard
    def get_dataset(self, overwrite: bool = False) -> None:
        raise NotImplementedError


RE_EXDC = re.compile(r"\.exdc[\S\s]*?\.end", re.MULTILINE)


def remove_exdc(fp: Path) -> None:
    t = fp.read_text()
    t = RE_EXDC.sub(".end", t)
    fp.write_text(t)


RE_LATCH_IMPLICIT_CONTROL = re.compile(r"\.latch\s+(\S+)\s+(\S+)\s+([0,1,2,3])")


def find_implicit_latches(fp: Path) -> list[re.Match]:
    t = fp.read_text()
    matches = list(RE_LATCH_IMPLICIT_CONTROL.finditer(t))
    return matches


def add_implicit_global_clock(fp: Path) -> None:
    t = fp.read_text()
    lines = t.splitlines()
    lines_striped = [line.strip() for line in lines]
    matches = find_implicit_latches(fp)
    models = set()
    for match in matches:
        model_line = None
        for line in t[: match.start()].splitlines()[::-1]:
            if line.startswith(".model"):
                model_line = line
                break
        if model_line is None:
            raise ValueError("Could not find model line for latch")
        model_name = model_line.split(" ")[1]
        models.add(model_name)

    # for each model, add a global clock
    for model in models:
        model_line_idx = lines_striped.index(f".model {model}")
        # find the next line that starts with .outputs
        outputs_line_idx = model_line_idx
        for i in range(model_line_idx + 1, len(lines_striped)):
            if lines_striped[i].startswith(".") and not lines_striped[i].startswith(".inputs"):
                outputs_line_idx = i
                break
        if outputs_line_idx == model_line_idx:
            raise ValueError("Could not find .outputs line for latch")

        # insert the global clock
        lines.insert(outputs_line_idx, ".inputs clk")

    t = "\n".join(lines)

    # for each latch, add the global clock
    for match in matches:
        latch_line_new = f".latch {match.group(1)} {match.group(2)} re clk {match.group(3)}"
        t = t.replace(match.group(0), latch_line_new)

    fp.write_text(t)


class MCNC20DatasetRetriever(DataRetriever):
    dataset_name: str = "mcnc20"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    DATA_URL: str = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/MCNC.7z"

    BLACKLIST: ClassVar[list[str]] = [
        "alu3",
    ]

    @staticmethod
    def fix_missing_end(fp: Path) -> None:
        t = fp.read_text()
        t += "\n.end"
        fp.write_text(t)

    def get_dataset(self, overwrite: bool = False, timeout: int = 30) -> None:
        # check for yosys
        yosys_bin = auto_find_bin("yosys")
        if yosys_bin is None:
            raise RuntimeError(
                f"Yosys is needed to preprocess the {self.dataset_name} dataset. "
                "Yosys was not found in PATH or in the "
                "YOSYS_PATH environment variable.",
            )

        r = requests.get(self.DATA_URL, timeout=timeout)
        if r.status_code != requests.codes.ok:
            raise RuntimeError(f"Failed to download {self.dataset_name} dataset")

        with py7zr.SevenZipFile(io.BytesIO(r.content), "r") as archive:
            design_files = [p for p in archive.getnames() if p.endswith(".blif")]
            for design_file in design_files:
                name = design_file.split("/")[-1].removesuffix(".blif")
                design_name = f"mcnc20__{name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_tags"] = self.dataset_tags
                metadata_fp = design_dir / "design.json"
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_blif_file_dir = design_dir / "sources_blif"
                source_blif_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[design_file], path=source_blif_file_dir)
                archive.reset()

                current_fp = source_blif_file_dir / Path(design_file)
                new_fp = source_blif_file_dir / Path(design_file).name
                current_fp.rename(new_fp)

                if ".exdc" in new_fp.read_text():
                    remove_exdc(new_fp)

                if name in {"i10", "i2", "i3", "i4", "i5", "i6", "i7"}:
                    self.fix_missing_end(new_fp)

                if find_implicit_latches(new_fp):
                    add_implicit_global_clock(new_fp)

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)

                yosys_script = f"""
                read_blif -sop {source_blif_file_dir / new_fp}
                proc
                techmap t:$sop
                # techmap t:$ff
                # check
                write_verilog {source_file_dir / name}.v
                """

                temp_dir_yosys = TemporaryDirectory()
                temp_dir_fp_yosys = Path(temp_dir_yosys.name)
                temp_script_fp = temp_dir_fp_yosys / "script.ys"
                temp_script_fp.write_text(yosys_script)

                p = subprocess.run(
                    [yosys_bin, "-s", temp_script_fp],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if p.returncode != 0:
                    raise RuntimeError(
                        f"Yosys failed to convert {new_fp} to Verilog:\n{p.stdout}\n{p.stderr}\n",
                    )


class DeepBenchVerilogDatasetRetriever(DataRetriever):
    dataset_name: str = "deepbenchverilog"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    DESIGN_PATHS: ClassVar[list[str]] = [
        # inference
        # inference/Conv
        # "verilog/inference/Conv/conv_b1_in_112_112_3_f_7_7_16_s_2_p_same",
        "verilog/inference/Conv/conv_b1_in_112_112_3_f_7_7_16_s_2_p_same/ap_fixed_16_8",
        "verilog/inference/Conv/conv_b1_in_112_112_3_f_7_7_16_s_2_p_same/ap_fixed_8_4",
        # "verilog/inference/Conv/conv_b1_in_56_56_16_f_1_1_64_s_2_p_valid",
        "verilog/inference/Conv/conv_b1_in_56_56_16_f_1_1_64_s_2_p_valid/ap_fixed_16_8",
        "verilog/inference/Conv/conv_b1_in_56_56_16_f_1_1_64_s_2_p_valid/ap_fixed_8_4",
        # "verilog/inference/Conv/conv_b2_in_7_7_32_f_1_1_128_s_1_p_valid",
        "verilog/inference/Conv/conv_b2_in_7_7_32_f_1_1_128_s_1_p_valid/ap_fixed_16_8",
        "verilog/inference/Conv/conv_b2_in_7_7_32_f_1_1_128_s_1_p_valid/ap_fixed_8_4",
        # inference/GEMM
        "verilog/inference/GEMM/GEMM_3072_3000_1024_N_N_Core_256_200_256",
        "verilog/inference/GEMM/GEMM_35_700_2048_N_N_Core_35_175_256",
        "verilog/inference/GEMM/GEMM_5124_700_2048_N_N_Core_244_175_256",
        "verilog/inference/GEMM/GEMM_512_6000_2816_N_N_Core_256_200_256",
        # inference/RNN
        "verilog/inference/RNN/LSTM_256_4_Core_256_4_256_Reuse_4_1_2",
        "verilog/inference/RNN/LSTM_1536_4_Core_256_4_256_Reuse_24_1_12",
        "verilog/inference/RNN/GRU_2560_2_Core_256_2_256_Reuse_30_1_20",
        "verilog/inference/RNN/GRU_2816_1_Core_256_1_256_Reuse_33_1_22",
        # training
        # training/Conv
        "verilog/training/Conv/conv_b16_in_28_28_16_f_5_5_8_s_1_p_same",
        "verilog/training/Conv/conv_b16_in_56_56_3_f_3_3_16_s_1_p_same",
        "verilog/training/Conv/conv_b16_in_7_7_16_f_3_3_16_s_1_p_same",
        "verilog/training/Conv/conv_b8_in_28_28_16_f_3_3_16_s_1_p_same",
        # training/GEMM
        "verilog/training/GEMM/GEMM_1760_128_1760_N_N_Core_220_128_220",
        "verilog/training/GEMM/GEMM_1760_128_1760_N_N_Core_352_128_352_extra",
        "verilog/training/GEMM/GEMM_2560_64_2560_N_N_Core_256_64_256",
        "verilog/training/GEMM/GEMM_3072_128_1024_T_N_Core_256_128_256",
        "verilog/training/GEMM/GEMM_5124_9124_2560_T_N_Core_244_256_256",
        "verilog/training/GEMM/GEMM_7860_648_2560_N_N_Core_131_64_256",
        # training/RNN
        "verilog/training/RNN/LSTM_1024_128_Core_256_128_256_Reuse_16_1_8",
        "verilog/training/RNN/LSTM_2816_32_Core_256_32_256_Reuse_33_1_22",
        "verilog/training/RNN/Vanilla_1760_16_Core_220_16_220_Reuse_8_1_12",
        "verilog/training/RNN/Vanilla_2560_32_Core_256_32_256_Reuse_10_1_20",
    ]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader("DeepBenchVerilog", "raminrasoulinezhad")
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(self.DESIGN_PATHS)

        for gh_path in self.DESIGN_PATHS:
            if "inference/Conv" in gh_path:
                base_name_split = gh_path.split("/")[-2:]
                base_name = "_".join(base_name_split)
            else:
                base_name = gh_path.split("/")[-1]

            scaffold = build_design_scaffolding(
                self.design_dataset.designs_dir,
                base_name,
                "deepbenchverilog",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffold.source_dir

            path_on_disk = gfd.get_path_on_disk(gh_path)
            listing = sorted(path_on_disk.iterdir())
            for file in listing:
                if file.is_dir():
                    raise ValueError("Expected a file, got a directory")
                shutil.copy(file, source_file_dir)

        gfd.cleanup()


class RegexFsmVerilogDatasetRetriever(DataRetriever):
    dataset_name: str = "regex_fsm_verilog"
    dataset_tags: ClassVar[list[str]] = ["synthetic"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader("regex-fsm-verilog", "stefanpie")
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/generated_designs.tar.gz"])

        file_on_disk = gfd.get_path_on_disk("generated_designs.tar.gz")
        archive = tarfile.open(file_on_disk)

        design_dirs = [p.split("/")[1] for p in archive.getnames() if p.count("/") == 1]
        for design_dir in design_dirs:
            scaffold = build_design_scaffolding(
                self.design_dataset.designs_dir,
                design_dir,
                "regex_fsm_verilog",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffold.source_dir

            v_str_io = archive.extractfile(f"generated_designs/{design_dir}/fsm.v")
            if v_str_io is None:
                raise ValueError(f"Could not find fsm.v for {design_dir}")
            v_str = v_str_io.read().decode()

            design_fp = source_file_dir / "fsm.v"
            design_fp.write_text(v_str)

        archive.close()
        gfd.cleanup()


class XACTDatasetRetriever(DataRetriever):
    dataset_name: str = "xact"
    dataset_tags: ClassVar[list[str]] = ["benchmark", "reference"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader("xact-designs", "stefanpie")
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/designs_converted.zip"])

        file_on_disk = gfd.get_path_on_disk("designs_converted.zip")
        archive = zipfile.ZipFile(file_on_disk)

        design_dirs_set = {path_str.split("/")[0].strip() for path_str in archive.namelist()}
        design_dirs = sorted(design_dirs_set)

        for design_dir in design_dirs:
            scaffold = build_design_scaffolding(
                self.design_dataset.designs_dir,
                design_dir,
                "xact",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffold.source_dir
            design_dir_fp = scaffold.design_dir_fp

            verilog_files = [
                "vlib.v",
                f"{design_dir}.v",
            ]

            for verilog_file in verilog_files:
                v_str_io = archive.open(f"{design_dir}/{verilog_file}")
                v_str = v_str_io.read().decode()

                design_fp = source_file_dir / verilog_file
                design_fp.write_text(v_str)

            top_str_io = archive.open(f"{design_dir}/top.txt")
            top_str = top_str_io.read().decode()
            top_fp = design_dir_fp / "top.txt"
            top_fp.write_text(top_str)

        archive.close()
        gfd.cleanup()


class EspressoPLADatasetRetriever(DataRetriever):
    dataset_name: str = "espresso_pla"
    dataset_tags: ClassVar[list[str]] = ["benchmark", "reference"]

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader("espresso-pla-designs-verilog", "stefanpie")
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(["/generated_designs.tar.gz"])

        file_on_disk = gfd.get_path_on_disk("generated_designs.tar.gz")
        archive = tarfile.open(file_on_disk)

        design_dirs = [p.split("/")[1] for p in archive.getnames() if p.count("/") == 2]
        for design_dir in design_dirs:
            scaffolding = build_design_scaffolding(
                self.design_dataset.designs_dir,
                design_dir,
                "espresso_pla",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffolding.source_dir
            design_dir_fp = scaffolding.design_dir_fp

            # each is a dir with verilog files in it
            v_str_io = archive.extractfile(f"generated_designs/{design_dir}/{design_dir}.v")
            if v_str_io is None:
                raise ValueError(f"Could not find {design_dir}.v for {design_dir}")
            v_str = v_str_io.read().decode()

            design_fp = source_file_dir / f"{design_dir}.v"
            design_fp.write_text(v_str)

            # write a top_file with the top module name
            top_fp = design_dir_fp / "top.txt"
            top_fp.write_text(f"{design_dir}")

        archive.close()
        gfd.cleanup()


class FPGAMicroBenchmarksDatasetRetriever(DataRetriever):
    dataset_name: str = "fpga_micro_benchmarks"
    dataset_tags: ClassVar[list[str]] = ["benchmark"]

    REPO_OWNER: ClassVar[str] = "tangxifan"
    REPO_NAME: ClassVar[str] = "micro_benchmark"

    DESIGN_PATHS_SINGLE_FILE: ClassVar[list[str]] = [
        "simple_registers/signal_gen/clock_divider.v",
        "simple_registers/signal_gen/pulse_generator.v",
        "simple_registers/signal_gen/reset_generator.v",
        "ram/pipelined_8bit_adder/pipelined_8bit_adder.v",
    ]

    DESIGN_PATHS_MULTI_FILE: ClassVar[dict[str, list[str]]] = {
        "FSM_three_code": [
            "fsm/FSM_three_code/FSM_hour.v",
            "fsm/FSM_three_code/FSM_minute.v",
            "fsm/FSM_three_code/FSM_second.v",
            "fsm/FSM_three_code/FSM_top.v",
        ],
    }

    DESIGN_PATHS_SINGLE_DIR: ClassVar[list[tuple[str, str]]] = [
        ("simple_registers_blinking", "simple_registers/blinking"),
        ("simple_registers_clk_divider", "simple_registers/clk_divider"),
        ("simple_registers_ff_dffnr", "simple_registers/ff/dffnr"),
        ("simple_registers_pwm_generator", "simple_registers/pwm_generator"),
        ("simple_gates_and2", "simple_gates/and2"),
        ("simple_gates_and2_latch", "simple_gates/and2_latch"),
        ("simple_gates_and2_latch_2clock", "simple_gates/and2_latch_2clock"),
        ("simple_gates_and2_latch_2clock", "simple_gates/and2_latch_2clock"),
        ("simple_gates_and2_or2", "simple_gates/and2_or2"),
        ("simple_gates_and2_pipelined", "simple_gates/and2_pipelined"),
        ("simple_gates_and4", "simple_gates/and4"),
        ("simple_gates_or2", "simple_gates/or2"),
        ("ram_asyn_spram_4x1", "ram/asyn_spram_4x1"),
        ("ram_dual_port_ram_16k", "ram/dual_port_ram_16k"),
        ("ram_dual_port_ram_1k", "ram/dual_port_ram_1k"),
        ("ram_fifo", "ram/fifo/rtl"),
        ("ram_syn_spram_4x1", "ram/syn_spram_4x1"),
        ("processors_VexRiscv_full", "processors/VexRiscv_full/rtl"),
        ("processors_VexRiscv_murax", "processors/VexRiscv_murax/rtl"),
        ("processors_VexRiscv_small", "processors/VexRiscv_small/rtl"),
        ("interface_SAPone", "interface/SAPone/rtl"),
        ("interface_cf_ldpc", "interface/cf_ldpc/rtl"),
        ("interface_opencores_can", "interface/opencores_can/rtl/verilog"),
        ("interface_opencores_gpio", "interface/opencores_gpio/rtl"),
        ("interface_opencores_i2c", "interface/opencores_i2c/rtl"),
        ("interface_opencores_ptc", "interface/opencores_ptc/rtl"),
        ("interface_opencores_simple_spi", "interface/opencores_simple_spi/rtl"),
        ("interface_opencores_uart16550", "interface/opencores_uart16550/rtl"),
        ("interface_routing_test", "interface/routing_test"),
        ("interface_rtcclock", "interface/rtcclock/rtl"),
        ("interface_sockit_owm", "interface/sockit_owm/rtl"),
        ("interface_spimaster", "interface/spimaster/rtl"),
        ("interface_test_mode_low", "interface/test_mode_low"),
        ("interface_test_modes_k4_N4", "interface/test_modes/k4_N4"),
        ("interface_test_modes_k6_N10", "interface/test_modes/k6_N10"),
        ("interface_uberddr3", "interface/uberddr3/rtl"),
        ("interface_verilog_spi", "interface/verilog_spi/rtl"),
        ("interface_wb_lcd", "interface/wb_lcd/rtl"),
        ("interface_wb_lcd_ramless", "interface/wb_lcd_ramless/rtl"),
        ("interface_wb_rs232_syscon", "interface/wb_rs232_syscon/rtl"),
        ("interface_wbi2c", "interface/wbi2c"),
        ("interface_wbqspiflash", "interface/wbqspiflash/rtl"),
        ("interface_wbscope", "interface/wbscope/rtl"),
        ("interface_wbspi_master", "interface/wbspi_master/rtl"),
        ("interface_wbuart32", "interface/wbuart32/rtl"),
        ("fsm_fsm_seq_detector", "fsm/fsm_seq_detector"),
        ("fsm_scalable_seq_detector", "fsm/scalable_seq_detector"),
        ("dsp_FIR_filter", "dsp/FIR_filter"),
        ("dsp_cordic", "dsp/cordic/rtl"),
        ("dsp_cordic_core", "dsp/cordic_core"),
        ("dsp_cr_div", "dsp/cr_div/rtl"),
        ("dsp_cr_div", "dsp/cr_div/rtl"),
        ("dsp_mult_mult_2_pipelined", "dsp/mult/mult_2_pipelined"),
        ("dsp_pid_controller", "dsp/pid_controller/rtl"),
        ("dsp_signed_integer_divider", "dsp/signed_integer_divider/rtl"),
        ("simple_gates_adder_4", "simple_gates/adder/adder_4"),
        ("simple_gates_adder_6", "simple_gates/adder/adder_6"),
        ("simple_gates_adder_16", "simple_gates/adder/adder_16"),
    ]

    DESIGN_PATHS_COLLECTION: ClassVar[list[str]] = [
        "simple_registers/counters",
        "dsp/mac",
    ]

    def get_single_file_designs(self, gfd: GithubFastDownloader, overwrite: bool = False) -> None:
        for gh_path in self.DESIGN_PATHS_SINGLE_FILE:
            scaffolding = build_design_scaffolding(
                self.design_dataset.designs_dir,
                Path(gh_path).stem,
                "fpga_micro_benchmarks",
                self.dataset_name,
                self.dataset_tags,
            )

            source_file_dir = scaffolding.source_dir

            text_fp = gfd.get_path_on_disk(gh_path)
            shutil.copy(text_fp, source_file_dir)

    def get_multi_file_designs(self, gfd: GithubFastDownloader, overwrite: bool = False) -> None:
        for d_name, gh_paths in self.DESIGN_PATHS_MULTI_FILE.items():
            scaffolding = build_design_scaffolding(
                self.design_dataset.designs_dir,
                d_name,
                "fpga_micro_benchmarks",
                self.dataset_name,
                self.dataset_tags,
            )
            source_file_dir = scaffolding.source_dir

            for gh_path in gh_paths:
                text_fp = gfd.get_path_on_disk(gh_path)
                shutil.copy(text_fp, source_file_dir)

    def get_one_single_dir(
        self,
        gfd: GithubFastDownloader,
        design_name_base: str,
        gh_design_dir: str,
        ignore_tb_files: bool = False,
    ) -> None:
        scaffolding = build_design_scaffolding(
            self.design_dataset.designs_dir,
            design_name_base,
            "fpga_micro_benchmarks",
            self.dataset_name,
            self.dataset_tags,
        )

        source_file_dir = scaffolding.source_dir

        path_on_disk = gfd.get_path_on_disk(gh_design_dir)
        listing = sorted(path_on_disk.iterdir())

        files_hdl: list[Path] = []
        for listing_item in listing:
            if listing_item.is_file() and Path(listing_item.name).suffix in SOURCE_FILES_EXTENSIONS_SET:
                files_hdl.append(listing_item)

        def tb_filter(file_hdl: Path) -> bool:
            return not Path(file_hdl.name).stem.endswith("_tb")

        if ignore_tb_files:
            files_hdl = [f for f in files_hdl if tb_filter(f)]

        for file_hdl in files_hdl:
            shutil.copy(file_hdl, source_file_dir)

    def get_designs_single_dir(self, gfd: GithubFastDownloader, overwrite: bool = False) -> None:
        for design_name, gh_design_dir in self.DESIGN_PATHS_SINGLE_DIR:
            self.get_one_single_dir(
                gfd,
                design_name,
                gh_design_dir,
            )

    def get_designs_collections(self, gfd: GithubFastDownloader, overwrite: bool = False) -> None:
        for dir_collection in self.DESIGN_PATHS_COLLECTION:
            path_on_disk = gfd.get_path_on_disk(dir_collection)
            listing = sorted(path_on_disk.iterdir())
            subdirs = [p for p in listing if p.is_dir()]
            for design_subdir in subdirs:
                self.get_one_single_dir(
                    gfd,
                    design_subdir.name,
                    str(design_subdir.relative_to(gfd.repo_dir)),
                    ignore_tb_files=True,
                )

    def get_dataset(self, overwrite: bool = False) -> None:
        gfd = GithubFastDownloader(self.REPO_NAME, self.REPO_OWNER)
        gfd.clone_repo()
        gfd.enable_sparse_checkout()
        gfd.checkout_stuff(
            ["/dsp/", "/fsm/", "/interface/", "/processors/", "/ram/", "/simple_gates/", "/simple_registers/"],
        )

        self.get_designs_collections(gfd, overwrite=overwrite)
        self.get_designs_single_dir(gfd, overwrite=overwrite)
        self.get_multi_file_designs(gfd, overwrite=overwrite)
        self.get_single_file_designs(gfd, overwrite=overwrite)

        gfd.cleanup()
