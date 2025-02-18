import logging
import multiprocessing
from pathlib import Path

import pytest
from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import (
    DataRetriever,
    # ISCAS85DatasetRetriever,
    OpencoresDatasetRetriever,
)
from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.vivado.flow_vivado import (
    FlowSettingsXilinxVivado,
    PartXilinx,
    ToolBinsXilinxVivado,
    XilinxVivadoFlow,
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
db_path = test_path / "db_testing_xilinx"
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
    # ISCAS85DatasetRetriever,
    OpencoresDatasetRetriever,
]

devices = [
    "xc7a100tfgg676-2",
]

tool_bins = ToolBinsXilinxVivado.auto_find_bins()
tool_settings = FlowSettingsXilinxVivado()


def run_single(d: DesignDataset, design: dict[str, str], flow: XilinxVivadoFlow) -> None:
    flow.build_flow_single(design)
    design_dir = d.designs_dir / design["design_name"]
    bitstream_file = design_dir / "flows" / flow.flow_name / "design.bit"
    assert bitstream_file.exists()


@pytest.mark.parametrize("device", devices)
@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_xilinx_flow(device: str, data_retriever: type[DataRetriever]) -> None:
    r = data_retriever(d)
    auto_retriever(d, r.__class__)

    part = PartXilinx(device=device)
    flow = XilinxVivadoFlow(d, part, tool_bins, tool_settings)

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
