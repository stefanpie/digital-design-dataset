import json
import operator
import os
import re
import shutil
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from github import Auth, Github

VERILOG_SOURCE_EXTENSIONS = [".v", ".sv", ".svh", ".vh", ".h", ".inc"]
VERILOG_SOURCE_EXTENSIONS_SET = set(VERILOG_SOURCE_EXTENSIONS) | {ext.upper() for ext in VERILOG_SOURCE_EXTENSIONS}

HARDWARE_DATA_TEXT_EXTENSIONS = [".coe", ".mif", ".mem"]
HARDWARE_DATA_TEXT_EXTENSIONS_SET = set(HARDWARE_DATA_TEXT_EXTENSIONS) | {
    ext.upper() for ext in HARDWARE_DATA_TEXT_EXTENSIONS
}

SOURCE_FILES_EXTENSIONS_SET = VERILOG_SOURCE_EXTENSIONS_SET | HARDWARE_DATA_TEXT_EXTENSIONS_SET

# === General Notes and TODOs ===
# - Refactor this to multiple files, one for metaobjects,
#   one for dataset retrievers, one for flows, ...
#
# - Make sure type hints are comprehensive
#
# - Use pydantic to enfore a dataset stucture and metadata structure,
#   this reuires non-trivial changes but is worth it


class DirectoryNotEmptyError(FileExistsError):
    pass


def make_dir_if_not_empty(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif len(os.listdir(path)) > 0:
        raise DirectoryNotEmptyError(
            "Directory is not empty. Support for partially constructed datasets is not implemented yet.",
        )


def build_metadata(
    design_name: str,
    dataset_name: str,
    dataset_tags: list[str],
    dir_to_write: Path | None = None,
    default_filename: str = "design.json",
) -> tuple[dict, Path | None]:
    metadata: dict[str, str | list[str]] = {}
    metadata["design_name"] = design_name
    metadata["dataset_name"] = dataset_name
    metadata["dataset_tags"] = dataset_tags
    if dir_to_write is not None:
        if not dir_to_write.exists():
            raise ValueError(f"Directory {dir_to_write} does not exist")
        metadata_fp = dir_to_write / default_filename
        metadata_fp.write_text(json.dumps(metadata, indent=4))
    else:
        metadata_fp = None
    return metadata, metadata_fp


def build_individual_design_dir(
    dataset_designs_dir: Path,
    design_name: str,
) -> Path:
    design_dir_fp = dataset_designs_dir / design_name
    if design_dir_fp.exists():
        shutil.rmtree(design_dir_fp)
    design_dir_fp.mkdir(parents=True, exist_ok=True)
    return design_dir_fp


def build_sources_dir(
    design_dir_fp: Path,
    sources_dir_name: str = "sources",
) -> Path:
    if not design_dir_fp.exists():
        raise ValueError(f"Design directory {design_dir_fp} does not exist")
    source_file_dir = design_dir_fp / sources_dir_name
    source_file_dir.mkdir()
    return source_file_dir


@dataclass
class DesignScaffoldingOutput:
    design_name: str
    design_dir_fp: Path
    metadata: dict
    metadata_fp: Path
    source_dir: Path


def build_design_scaffolding(
    dataset_designs_dir: Path,
    design_name_base: str,
    design_name_prefix: str,
    dataset_name: str,
    dataset_tags: list[str],
    sources_dir_name: str = "sources",
    metadata_filename: str = "design.json",
):
    design_name = f"{design_name_prefix}__{design_name_base}"
    design_dir_fp = build_individual_design_dir(dataset_designs_dir, design_name)
    metadata, metadata_fp = build_metadata(
        design_name,
        dataset_name,
        dataset_tags,
        dir_to_write=design_dir_fp,
        default_filename=metadata_filename,
    )
    if metadata_fp is None:
        raise ValueError("metadata_fp is None, not supposed to happen")
    source_dir = build_sources_dir(design_dir_fp, sources_dir_name)
    return DesignScaffoldingOutput(
        design_name=design_name,
        design_dir_fp=design_dir_fp,
        metadata=metadata,
        metadata_fp=metadata_fp,
        source_dir=source_dir,
    )


class DesignDataset:
    def __init__(
        self,
        dataset_dir: Path,
        overwrite: bool = False,
        gh_token: str | None = None,
    ) -> None:
        self.dataset_dir = dataset_dir

        if overwrite and self.dataset_dir.exists():
            shutil.rmtree(self.dataset_dir)

        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.designs_dir.mkdir(parents=True, exist_ok=True)

        self.gh_token = gh_token
        if self.gh_token is not None:
            self.gh_api = Github(auth=Auth.Token(self.gh_token))
        else:
            self.gh_api = Github()

    @property
    def root_dir(self) -> Path:
        return self.dataset_dir

    @property
    def designs_dir(self) -> Path:
        return self.dataset_dir / "designs"

    @property
    def index_path(self) -> Path:
        return self.dataset_dir / "index.json"

    @property
    def does_index_exist(self) -> bool:
        return self.index_path.exists()

    @property
    def index(self) -> list[dict]:
        # sorted by "design_name"
        designs = []
        for design_dir in self.designs_dir.iterdir():
            design_json_fp = design_dir / "design.json"
            with design_json_fp.open() as f:
                design = json.load(f)
            designs.append(design)
        designs = sorted(designs, key=operator.itemgetter("design_name"))
        return designs

    @property
    def index_generator(self) -> Iterator[dict]:
        # not guaranteed to be in sorted by "design_name"
        for design_dir in self.designs_dir.iterdir():
            design_json_fp = design_dir / "design.json"
            with design_json_fp.open() as f:
                design = json.load(f)
            yield design

    def summary(self) -> str:
        summary = f"Dataset at {self.dataset_dir}\n"
        summary += f"Number of designs: {len(self.index)}\n"
        dataset_name_counter = Counter(design["dataset_name"] for design in self.index)
        summary += "Datasets + Design Counts:\n"
        for dataset_name, count in dataset_name_counter.items():
            summary += f"    {dataset_name}: {count}\n"
        return summary

    def print_summary(self) -> None:
        print(self.summary())  # noqa: T201

    def get_design_metadata_by_design_name(self, design_name: str) -> dict | None:
        """Retrieves the metadata of a design based on its design name.

        Args:
        ----
            design_name (str): The name of the design.

        Returns:
        -------
            dict | None: The metadata of the design if found, None otherwise.

        """
        metadata = None
        for design in self.index:
            if design["design_name"] == design_name:
                metadata = design
                break
        return metadata

    def get_design_metadata_by_design_name_regex(
        self,
        design_name_regex_pattern: str,
    ) -> list[dict]:
        """Retrieves the design metadata for designs whose names match the given
        regular expression pattern.

        Args:
        ----
            design_name_regex_pattern (str): The regular expression pattern to
            match against design names.

        Returns:
        -------
            list[dict]: A list of dictionaries containing the metadata of
            designs that match the pattern.

        """
        metadata = [design for design in self.index if re.match(design_name_regex_pattern, design["design_name"])]
        return metadata

    def get_design_metadata_by_dataset_name(self, dataset_name: str) -> list[dict]:
        """Retrieves all design metadata for designs in a given dataset,
        identified by the dataset name.

        Args:
        ----
            dataset_name (str): The name of the dataset.

        Returns:
        -------
            list[dict]: A list of design metadata dictionaries matching the
            given dataset name.

        """
        metadata = [design for design in self.index if design["dataset_name"] == dataset_name]
        return metadata

    def get_design_source_files(self, design_name: str) -> list[Path]:
        """Retrieves the source files for a given design name.

        Args:
        ----
            design_name (str): The name of the design.

        Returns:
        -------
            list[Path]: A list of Path objects representing the source files.

        """
        design_sources_dir = self.designs_dir / design_name / "sources"
        source_files = list(design_sources_dir.iterdir())
        return source_files

    def delete_design(self, design_name: str) -> None:
        design = self.get_design_metadata_by_design_name(design_name)
        if design is None:
            raise ValueError(f"Design {design_name} not found in dataset.")
        design_dir = self.designs_dir / design_name
        shutil.rmtree(design_dir)

    def delete_multiple_designs(self, design_names: list[str]) -> None:
        for design_name in design_names:
            self.delete_design(design_name)

    def delete_all_designs(self) -> None:
        shutil.rmtree(self.designs_dir)
        self.designs_dir.mkdir()
