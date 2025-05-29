import json
import operator
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import OpencoresDatasetRetriever
from digital_design_dataset.design_dataset import (
    DesignDataset,
)
from digital_design_dataset.flows.clock_detect import ClockDetectFlow
from tests.utils import load_common_test_env_vars

DIR_CURRENT = Path(__file__).parent


# load config data
env_config = dotenv_values(DIR_CURRENT / ".env")
gh_token, test_path, n_jobs = load_common_test_env_vars(DIR_CURRENT / ".env")


db_path = test_path / "db_test_clock_detect"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)

retrivers = [
    OpencoresDatasetRetriever,
]


def get_designs() -> list[dict]:
    designs_all: list[dict[str, Any]] = []
    for retriever in retrivers:
        r = retriever(d)
        dataset_name = r.dataset_name
        designs_to_remove = d.get_design_metadata_by_dataset_name(dataset_name)
        for design in designs_to_remove:
            d.delete_design(design["design_name"])
        r.get_dataset()
        designs = d.get_design_metadata_by_dataset_name(dataset_name)
        designs = sorted(designs, key=operator.itemgetter("design_name"))
        designs_all.extend(designs)
    return designs_all


def test_clock_detect():
    print("Retrieving designs")
    designs = get_designs()
    n_designs = len(designs)

    f = ClockDetectFlow(d)

    # filter fopr only opencores__dpsfmnce
    designs = [design for design in designs if design["design_name"] == "opencores__dpsfmnce"]

    # for i, design in enumerate(designs):
    #     design_name = design["design_name"]
    #     design_dir = d.designs_dir / design_name
    #     sources_dir = design_dir / "sources"

    #     print(f"{i + 1}/{n_designs} - {design_name} ({design_dir})")
    #     f.build_flow_single(design, overwrite=True)

    f.build_flow(overwrite=True, n_jobs=n_jobs)


def test_print_clock_detect():
    designs = d.index

    for design in designs:
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        clock_flow = design_dir / "flows" / "clock_detect"
        candidates_fp = clock_flow / "clock_candidates.json"
        assert candidates_fp.exists()
        clock_candidates = json.loads(candidates_fp.read_text())

        print(f"Design: {design_name}")
        if not clock_candidates:
            print("NONE")
        else:
            print(f"Clock candidates: {clock_candidates}")
        print()
