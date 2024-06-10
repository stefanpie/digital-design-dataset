import base64
import io
import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import py7zr
import requests
from github import Github
from github.ContentFile import ContentFile

from digital_design_dataset.design_dataset import (
    SOURCE_FILES_EXTENSIONS_SET,
    DesignDataset,
)


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
    if content == "":
        download_url = data.download_url
        r = requests.get(download_url, timeout=timeout)
        # if r.status_code != requests.status_codes.codes.ok:
        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
            )
        return r.content.decode("utf-8")
    return base64.b64decode(content).decode("utf-8")


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


class DatasetRetriever:
    dataset_name: str
    dataset_type: str  # TODO: Change to be more like tags, like a list[str]

    def __init__(self, design_dataset: DesignDataset) -> None:
        self.design_dataset = design_dataset

    def get_dataset(self, overwrite: bool = False) -> None:
        raise NotImplementedError

    def remove_dataset(self) -> None:
        designs = [
            d
            for d in self.design_dataset.index
            if d["dataset_name"] == self.dataset_name
        ]
        for design in designs:
            design_dir = self.design_dataset.designs_dir / design["design_name"]
            if design_dir.exists():
                shutil.rmtree(design_dir)


class OpencoresDatasetRetriever(DatasetRetriever):
    dataset_name = "opencores"
    dataset_type = "opencores"

    # https://github.com/stefanpie/hardware-design-dataset-opencores

    def get_dataset(self, overwrite: bool = False) -> None:
        download_url = get_file_download_url_from_github(
            self.design_dataset.gh_api,
            "stefanpie",
            "hardware-design-dataset-opencores",
            "designs.zip",
        )

        r = requests.get(download_url)  # TODO: add timeout
        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
            )
        z = zipfile.ZipFile(io.BytesIO(r.content))
        designs = []
        for fn in z.namelist():
            # get only top level folders "designs/*/"
            # folders may be nested, so we need to check if the folder
            # is a top level folder
            if (fn[-1] == "/") and (fn.count("/") == 2):
                designs.append(fn)

        for fn in designs:
            design_name = fn.split("/")[1]
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            aux_files_dir = design_dir / "aux_files"
            aux_files_dir.mkdir(parents=True, exist_ok=True)

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            for file in z.namelist():
                if file.startswith(f"designs/{design_name}/"):
                    if file[-1] != "/":
                        file_name = file.split("/")[-1]
                        extension = file_name.split(".")[-1]
                        if f".{extension}" in SOURCE_FILES_EXTENSIONS_SET:
                            fp = source_file_dir / file_name
                            fp.write_text(z.read(file).decode("utf-8"))
                        else:
                            fp = aux_files_dir / file_name
                            fp.write_text(z.read(file).decode("utf-8"))
        z.close()


class HW2VecDatasetRetriever(DatasetRetriever):
    dataset_name = "hw_2_vec"
    dataset_type = "academic"

    BLACKLIST = "RS232-T100"

    def get_dataset(self, overwrite: bool = False) -> None:
        download_url = get_file_download_url_from_github(
            self.design_dataset.gh_api,
            "AICPS",
            "hw2vec",
            "assets/datasets.zip",
        )

        r = requests.get(download_url)  # TODO: add timeout
        # if r.status_code != requests.status_codes.codes.ok:
        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
            )
        z = zipfile.ZipFile(io.BytesIO(r.content))
        designs = []
        for fn in z.namelist():
            if fn[-2:] == ".v":
                designs.append(fn)

        for fn in designs:
            design_name = fn.split("/")[-2]
            if design_name in self.BLACKLIST:
                continue
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)

            design_fp = source_file_dir / fn.split("/")[-1]
            design_fp.write_text(z.read(fn).decode("utf-8"))

        z.close()


class VTRDatasetRetriever(DatasetRetriever):
    dataset_name = "vtr"
    dataset_type = "academic"

    BLACKLIST = (
        "LU8PEEng",
        "LU32PEEng",
        "LU64PEEng",
        "boundtop",
        "mcml",
    )
    # these designs cause issues with yosys auto-expanding memories
    # leading to long runtimes and out-of-memory issues
    # TODO: find workaround in the future

    def get_dataset(self, overwrite: bool = True):
        listing = get_listing_from_github(
            self.design_dataset.gh_api,
            "verilog-to-routing",
            "vtr-verilog-to-routing",
            "vtr_flow/benchmarks/verilog",
        )

        file_list = []
        for content_file in listing:
            if (content_file.type == "file") and (content_file.name[-2:] == ".v"):
                file_list.append({
                    "name": content_file.name,
                    "path": content_file.path,
                    "url": content_file.download_url,
                })

        primitives_file_fp = "vtr_flow/primitives.v"
        primitives_file_txt = get_file_from_github(
            self.design_dataset.gh_api,
            "verilog-to-routing",
            "vtr-verilog-to-routing",
            primitives_file_fp,
        )
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
            design_name = file["name"].replace(".v", "")
            if design_name in self.BLACKLIST:
                continue
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)
            text = get_file_from_github(
                self.design_dataset.gh_api,
                "verilog-to-routing",
                "vtr-verilog-to-routing",
                file["path"],
            )

            design_fp = source_file_dir / file["name"]
            design_fp.write_text(text)

            design_primitives_fp = source_file_dir / "primitives.v"
            design_primitives_fp.write_text(primitives_file_txt)


class KoiosDatasetRetriever(DatasetRetriever):
    dataset_name = "koios"
    dataset_type = "academic"

    def get_dataset(self, overwrite: bool = False) -> None:
        listing = get_listing_from_github(
            self.design_dataset.gh_api,
            "verilog-to-routing",
            "vtr-verilog-to-routing",
            "vtr_flow/benchmarks/verilog/koios",
        )

        file_list = []
        for content_file in listing:
            if (content_file.type == "file") and (content_file.name[-2:] == ".v"):
                file_list.append({
                    "name": content_file.name,
                    "path": content_file.path,
                    "url": content_file.download_url,
                })

        file_list = list(filter(lambda x: "_include.v" not in x["name"], file_list))

        for file in file_list:
            design_name = file["name"].replace(".v", "")
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)
            text = get_file_from_github(
                self.design_dataset.gh_api,
                "verilog-to-routing",
                "vtr-verilog-to-routing",
                file["path"],
            )
            design_fp = source_file_dir / file["name"]
            design_fp.write_text(text)


class EPFLDatasetRetriever(DatasetRetriever):
    dataset_name = "epfl"
    dataset_type = "academic"

    def get_dataset(self, overwrite: bool = False) -> None:
        listing_0 = get_listing_from_github(
            self.design_dataset.gh_api,
            "lsils",
            "benchmarks",
            "arithmetic",
        )

        listing_1 = get_listing_from_github(
            self.design_dataset.gh_api,
            "lsils",
            "benchmarks",
            "random_control",
        )
        listing = listing_0 + listing_1

        file_list = []
        for content_file in listing:
            if (content_file.type == "file") and (content_file.name[-2:] == ".v"):
                file_list.append({
                    "name": content_file.name,
                    "path": content_file.path,
                    "url": content_file.download_url,
                })

        for file in file_list:
            design_name = file["name"].replace(".v", "")
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)
            text = get_file_from_github(
                self.design_dataset.gh_api,
                "lsils",
                "benchmarks",
                file["path"],
            )
            design_fp = source_file_dir / file["name"]
            design_fp.write_text(text)


class OPDBDatasetRetriever(DatasetRetriever):
    dataset_name = "opdb"
    dataset_type = "academic"

    def get_dataset(self, overwrite: bool = False) -> None:
        design_list = get_file_from_github(
            self.design_dataset.gh_api,
            "PrincetonUniversity",
            "OPDB",
            "modules/piton_baseline_designs.txt",
        )

        for design in design_list.splitlines():
            design_name = (
                "_".join(design.split("/")[1:]).replace(".v", "").replace(".pickle", "")
            )
            design_dir = self.design_dataset.designs_dir / design_name
            if design_dir.exists():
                shutil.rmtree(design_dir)
            design_dir.mkdir(parents=True, exist_ok=True)

            metadata = {}
            metadata["design_name"] = design_name
            metadata["dataset_name"] = self.dataset_name
            metadata["dataset_type"] = self.dataset_type
            metadata_fp = design_dir / "design.json"
            metadata_fp.write_text(json.dumps(metadata, indent=4))

            source_file_dir = design_dir / "sources"
            source_file_dir.mkdir(parents=True, exist_ok=True)
            text = get_file_from_github(
                self.design_dataset.gh_api,
                "PrincetonUniversity",
                "OPDB",
                design,
            )
            Path(source_file_dir / (design_name + ".v")).write_text(text)


class ISCAS85DatasetRetriever(DatasetRetriever):
    dataset_name: str = "iscas85"
    dataset_type: str = "academic"

    ISCAS_85_89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/ISCAS.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "iscas.7z"
        with requests.get(self.ISCAS_85_89_URL, stream=True) as r:
            with temp_file_fp.open("wb") as f:
                shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"Verilog/c.*?\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            isca85_verilog_files = [
                n for n in archive.getnames() if filter_pattern.match(n)
            ]

            for file_name in isca85_verilog_files:
                case_name = file_name.split("/")[-1].replace(".v", "")
                case_name = case_name.upper()
                design_name = f"iscas85_{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_type"] = self.dataset_type
                metadata_fp = design_dir / "design.json"
                # with open(metadata_fp, "w") as f:
                #     json.dump(metadata, f, indent=4)
                metadata_fp.write_text(json.dumps(metadata, indent=4))

                source_file_dir = design_dir / "sources"
                source_file_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(targets=[file_name], path=source_file_dir)
                archive.reset()

                current_fp = source_file_dir / Path(file_name)
                new_fp = source_file_dir / Path(file_name).name
                current_fp.rename(new_fp)
                shutil.rmtree(source_file_dir / "Verilog")


class ISCAS89DatasetRetriever(DatasetRetriever):
    dataset_name: str = "iscas89"
    dataset_type: str = "academic"

    ISCAS_85_89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/ISCAS.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "iscas.7z"
        with requests.get(self.ISCAS_85_89_URL, stream=True) as r:
            with temp_file_fp.open("wb") as f:
                shutil.copyfileobj(r.raw, f)

        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            extra_files = ["Verilog/lib.v", "Verilog/DFF2.v"]
            for file_name in extra_files:
                archive.extract(targets=[file_name], path=temp_dir_fp)
                archive.reset()

        filter_pattern = re.compile(r"Verilog/s.*?\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            isca85_verilog_files = [
                n for n in archive.getnames() if filter_pattern.match(n)
            ]

            for file_name in isca85_verilog_files:
                case_name = file_name.split("/")[-1].replace(".v", "")
                case_name = case_name.upper()
                design_name = f"iscas85_{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.dataset_name
                metadata["dataset_type"] = self.dataset_type
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


class LGSynth89DatasetRetriever(DatasetRetriever):
    name: str = "lgsynth89"
    type: str = "academic"

    LGSYNTH_89_URL = "https://ddd.fit.cvut.cz/www/prj/Benchmarks/LGSynth89.7z"

    def get_dataset(self, overwrite: bool = False) -> None:
        temp_dir = TemporaryDirectory()
        temp_dir_fp = Path(temp_dir.name)
        temp_file_fp = temp_dir_fp / "lgsynth89.7z"
        with requests.get(self.LGSYNTH_89_URL, stream=True) as r:
            with temp_file_fp.open("wb") as f:
                shutil.copyfileobj(r.raw, f)

        filter_pattern = re.compile(r"LGSynth89/Verilog/.*?_orig\.v")
        with py7zr.SevenZipFile(temp_file_fp, "r") as archive:
            lgsynth89_verilog_files = [
                n for n in archive.getnames() if filter_pattern.match(n)
            ]

            for file_name in lgsynth89_verilog_files:
                case_name = file_name.split("/")[-1].replace("_orig.v", "")
                design_name = f"lgsynth89_{case_name}"

                design_dir = self.design_dataset.designs_dir / design_name
                if design_dir.exists():
                    shutil.rmtree(design_dir)
                design_dir.mkdir(parents=True, exist_ok=True)

                metadata = {}
                metadata["design_name"] = design_name
                metadata["dataset_name"] = self.name
                metadata["dataset_type"] = self.type
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
