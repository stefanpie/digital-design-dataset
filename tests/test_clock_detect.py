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

DIR_CURRENT = Path(__file__).parent


# load config data
env_config = dotenv_values(DIR_CURRENT / ".env")

# load github token
gh_token = None
if "GITHUB_TOKEN" in env_config:
    gh_token = env_config["GITHUB_TOKEN"]

# load test path
if "TEST_DIR" not in env_config:
    raise ValueError("TEST_DIR not defined in .env file")
test_path_val = env_config["TEST_DIR"]
if not test_path_val:
    raise ValueError("TEST_DIR not defined in .env file")
test_path = Path(test_path_val)

# load n_jobs
if "N_JOBS" not in env_config:
    raise ValueError("N_JOBS not defined in .env file")
n_jobs_val = env_config["N_JOBS"]
if not n_jobs_val:
    raise ValueError("N_JOBS not defined in .env file")
try:
    n_jobs = int(n_jobs_val)
except ValueError as e:
    raise ValueError("N_JOBS must be an integer") from e
if n_jobs < 1:
    raise ValueError("N_JOBS must be greater than 0")


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
