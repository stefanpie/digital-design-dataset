import logging
import multiprocessing
import operator
from pathlib import Path

import pytest
from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import (
    DataRetriever,
    ISCAS85DatasetRetriever,
    OpencoresDatasetRetriever,
)
from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.quartus.flow_quartus import (
    AlteraPart,
    AlteraQuartusBins,
    AlteraQuartusFlow,
    AlteraQuartusFlowSettings,
    get_supported_devices_raw,
)
from digital_design_dataset.logger import build_logger

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


# load design dataset
db_path = test_path / "db_testing_quartus"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)

logger = build_logger("test_dataset_retrievers", logging.INFO)


def remove_existing_dataset_designs(d: DesignDataset, retriever_name: str) -> None:
    designs = d.get_design_metadata_by_dataset_name(retriever_name)
    for design in designs:
        d.delete_design(design["design_name"])


def auto_retriever(
    d: DesignDataset,
    retriever_class: type[DataRetriever],
) -> None:
    r = retriever_class(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


data_retrievers = [
    OpencoresDatasetRetriever,
]

devices = [
    "5CGTFD9E5F35C7",
]


tool_bins = AlteraQuartusBins.auto_find_bins()
tool_settings = AlteraQuartusFlowSettings()


def run_single(d: DesignDataset, design: dict[str, str], flow: AlteraQuartusFlow) -> None:
    flow.build_flow_single(design)
    design_dir = d.designs_dir / design["design_name"]
    sof_file = design_dir / "flows" / flow.flow_name / f"{design['design_name']}.sof"
    assert sof_file.exists()


@pytest.mark.parametrize("device", devices)
@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_quartus_flow(device: str, data_retriever: type[DataRetriever]) -> None:
    r = data_retriever(d)
    dataset_name = r.__class__.dataset_name
    designs = d.get_design_metadata_by_dataset_name(dataset_name)
    designs = sorted(designs, key=operator.itemgetter("design_name"))
    if not designs:
        r.get_dataset()
        designs = d.get_design_metadata_by_dataset_name(dataset_name)

    part = AlteraPart(device=device)
    flow = AlteraQuartusFlow(d, part, tool_bins, tool_settings)

    designs = d.get_design_metadata_by_dataset_name(data_retriever.dataset_name)

    if n_jobs == 1:
        for design in designs:
            run_single(d, design, flow)
    else:
        pool = multiprocessing.Pool(n_jobs)
        pool.starmap(
            run_single,
            [(d, design, flow) for design in designs],
            chunksize=1,
        )
        pool.close()
        pool.join()


def test_get_supported_parts_raw():
    parts = get_supported_devices_raw(AlteraQuartusBins.auto_find_quartus_sh())
    print(parts)

    assert parts
    assert len(parts) > 0
