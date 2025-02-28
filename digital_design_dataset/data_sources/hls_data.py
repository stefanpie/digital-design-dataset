import tarfile
import zipfile
from typing import ClassVar

from digital_design_dataset.data_sources.data_retrievers import DataRetriever
from digital_design_dataset.data_sources.github_fast_downloader import GithubFastDownloader
from digital_design_dataset.design_dataset import build_design_scaffolding


class PolybenchRetriever(DataRetriever):
    dataset_name: str = "polybench"
    dataset_tags: ClassVar[list[str]] = ["hls"]

    BENCHMARK_SETS: ClassVar = [
        "hls_polybench__fixed__mini__build.tar.gz",
        "hls_polybench__fixed__small__build.tar.gz",
        "hls_polybench__fixed__medium__build.tar.gz",
    ]

    def get_dataset(self, overwrite: bool = False, timeout: int = 30) -> None:
        gfd = GithubFastDownloader(
            "hls-polybench",
            "stefanpie",
        )

        gfd.clone_repo()
        gfd.enable_sparse_checkout()

        gfd.checkout_stuff([f"/dist/{bs}" for bs in self.BENCHMARK_SETS])

        for benchmark_set in self.BENCHMARK_SETS:
            set_type, set_size = benchmark_set.split("__")[1:3]

            file_on_disk = gfd.get_path_on_disk(f"dist/{benchmark_set}")
            targz = tarfile.open(file_on_disk, "r:gz")

            kernels = []
            for member in targz.getmembers():
                if member.name.count("/") == 0:
                    kernels.append(member.name)
            kernels = sorted(kernels)

            for kernel in kernels:
                design_name_kernel = kernel.replace("-", "_")

                base_name = f"{set_type}__{set_size}__{design_name_kernel}"

                scaffold = build_design_scaffolding(
                    self.design_dataset.designs_dir,
                    base_name,
                    "hls_polybench",
                    self.dataset_name,
                    self.dataset_tags,
                )
                source_file_dir = scaffold.source_dir

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

        gfd.cleanup()
