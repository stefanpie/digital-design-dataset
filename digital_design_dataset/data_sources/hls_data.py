import io
import json
import shutil
import tarfile
import zipfile
from typing import ClassVar

import requests

from digital_design_dataset.data_sources.data_retrievers import DataRetriever, get_file_download_url_from_github


class PolybenchRetriever(DataRetriever):
    dataset_name: str = "polybench"
    dataset_tags: ClassVar[list[str]] = ["hls"]

    BENCHMARK_SETS: ClassVar = [
        "hls_polybench__fixed__mini__build.tar.gz",
        "hls_polybench__fixed__small__build.tar.gz",
        "hls_polybench__fixed__medium__build.tar.gz",
    ]

    def get_dataset(self, _overwrite: bool = False, timeout: int = 30) -> None:
        for benchmark_set in self.BENCHMARK_SETS:
            set_type, set_size = benchmark_set.split("__")[1:3]

            download_url = get_file_download_url_from_github(
                self.design_dataset.gh_api,
                "stefanpie",
                "hls-polybench",
                f"dist/{benchmark_set}",
            )

            r = requests.get(
                download_url,
                timeout=timeout,
            )
            if r.status_code != requests.codes.ok:
                raise RuntimeError(
                    f"Failed to make request: {r.status_code}\n{r.text}\n{r.headers}",
                )

            targz = tarfile.open(fileobj=io.BytesIO(r.content))
            kernels = []
            for member in targz.getmembers():
                if member.name.count("/") == 0:
                    kernels.append(member.name)
            kernels = sorted(kernels)

            for kernel in kernels:
                design_name_kernel = kernel.replace("-", "_")
                design_name = f"{self.dataset_name}__{set_type}__{set_size}__{design_name_kernel}"

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

                # find the kernel/ip_*.zip file
                ip_zip_fp = f"{kernel}/ip_{kernel}.zip"
                ip_zip_data = targz.extractfile(ip_zip_fp)
                if ip_zip_data is None:
                    raise RuntimeError(f"Failed to find {ip_zip_fp} in {benchmark_set}")

                zip_file = zipfile.ZipFile(ip_zip_data)
                # get all files in the hdl/verilog/* directory
                for file in zip_file.namelist():
                    if file.startswith("hdl/verilog/"):
                        name = file.split("/")[-1]
                        new_fp = source_file_dir / name
                        new_fp.write_bytes(zip_file.read(file))
                zip_file.close()
                ip_zip_data.close()

            targz.close()
