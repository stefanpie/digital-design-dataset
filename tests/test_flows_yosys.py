import logging
import multiprocessing
from pathlib import Path

import pytest
from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import (
    DataRetriever,
    ISCAS85DatasetRetriever,
    # ISCAS85DatasetRetriever,
    OpencoresDatasetRetriever,
)
from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.flows import (
    YosysAIGFlow,
    YosysIntelSynthFlow,
    YosysLatticeSynthFlow,
    YosysSimpleSynthFlow,
    YosysXilinxSynthFlow,
)
from digital_design_dataset.logger import build_logger
from tests.utils import load_common_test_env_vars

DIR_CURRENT = Path(__file__).parent


# load config data
env_config = dotenv_values(DIR_CURRENT / ".env")
gh_token, test_path, n_jobs = load_common_test_env_vars(DIR_CURRENT / ".env")


# load design dataset
db_path = test_path / "db_testing_yosys"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)

logger = build_logger("test_flows_yosys", logging.INFO)


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


@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_yosys_simple_synth_flow(
    data_retriever: type[DataRetriever],
) -> None:
    auto_retriever(d, data_retriever)
    flow = YosysSimpleSynthFlow(d)
    flow.build_flow(n_jobs=n_jobs)


@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_yosys_synth_xilinx_flow(data_retriever: type[DataRetriever]) -> None:
    auto_retriever(d, data_retriever)
    flow = YosysXilinxSynthFlow(d)
    flow.build_flow(n_jobs=n_jobs)


@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_yosys_synth_intel_flow(data_retriever: type[DataRetriever]) -> None:
    auto_retriever(d, data_retriever)
    flow = YosysIntelSynthFlow(d)
    flow.build_flow(n_jobs=n_jobs)


@pytest.mark.parametrize("data_retriever", data_retrievers)
def test_yosys_synth_lattice_flow(data_retriever: type[DataRetriever]) -> None:
    auto_retriever(d, data_retriever)
    flow = YosysLatticeSynthFlow(d)
    flow.build_flow(n_jobs=n_jobs)
