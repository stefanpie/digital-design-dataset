import logging
import multiprocessing
import operator
from pathlib import Path

from dotenv import dotenv_values
from joblib import Parallel, delayed

from digital_design_dataset.data_sources.hls_data import PolybenchRetriever

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()

from digital_design_dataset.data_sources.data_retrievers import (
    AddersCVUTDatasetRetriever,
    DataRetriever,
    DeepBenchVerilogDatasetRetriever,
    EPFLDatasetRetriever,
    HW2VecDatasetRetriever,
    I99TDatasetRetriever,
    ISCAS85DatasetRetriever,
    ISCAS89DatasetRetriever,
    IWLS93DatasetRetriever,
    KoiosDatasetRetriever,
    LGSynth89DatasetRetriever,
    LGSynth91DatasetRetriever,
    MCNC20DatasetRetriever,
    OPDBDatasetRetriever,
    OpencoresDatasetRetriever,
    RegexFsmVerilogDatasetRetriever,
    VerilogAddersMongrelgemDatasetRetriever,
    VTRDatasetRetriever,
)
from digital_design_dataset.design_dataset import (
    DesignDataset,
)
from digital_design_dataset.flows.flows import Flow, ModuleInfoFlow, YosysAIGFlow
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
db_path = test_path / "db"
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


def run_single(
    design: dict,
    f_module: ModuleInfoFlow,
    f_synth: YosysAIGFlow,
    logger: logging.Logger,
) -> None:
    logger.info(f"{design['design_name']}: Running {f_module.__class__.__name__}")
    f_module.build_flow_single(design)

    logger.info(f"{design['design_name']}: Running {f_synth.__class__.__name__}")
    f_synth.build_flow_single(design)

    logger.info(f"{design['design_name']}: Done running flows")


def auto_validate(
    d: DesignDataset,
    retriever_class: type[DataRetriever],
    n_jobs: int = 1,
) -> None:
    if n_jobs < 1:
        raise ValueError("n_jobs must be greater than 0")

    r = retriever_class(d)
    dataset_name = r.__class__.dataset_name
    designs = d.get_design_metadata_by_dataset_name(dataset_name)
    designs = sorted(designs, key=operator.itemgetter("design_name"))
    if not designs:
        r.get_dataset()
        designs = d.get_design_metadata_by_dataset_name(dataset_name)

    f_module = ModuleInfoFlow(d)
    f_synth = YosysAIGFlow(d)

    if n_jobs == 1:
        for design in designs:
            run_single(design, f_module, f_synth, logger)
    else:
        pool = multiprocessing.Pool(n_jobs)
        pool.starmap(
            run_single,
            [(design, f_module, f_synth, logger) for design in designs],
            chunksize=1,
        )
        pool.close()
        pool.join()


### EPFLDatasetRetriever ###
def test_epfl_retriever() -> None:
    auto_retriever(d, EPFLDatasetRetriever)


def test_epfl_validate() -> None:
    auto_validate(d, EPFLDatasetRetriever, n_jobs=n_jobs)


### HW2VecDatasetRetriever ###
def test_hw2vec_retriever() -> None:
    auto_retriever(d, HW2VecDatasetRetriever)


def test_hw2vec_validate() -> None:
    auto_validate(d, HW2VecDatasetRetriever, n_jobs=n_jobs)


### ISCAS85DatasetRetriever ###
def test_iscas85_retriever() -> None:
    auto_retriever(d, ISCAS85DatasetRetriever)


def test_iscas85_validate() -> None:
    auto_validate(d, ISCAS85DatasetRetriever, n_jobs=n_jobs)


### ISCAS89DatasetRetriever ###
def test_iscas89_retriever() -> None:
    auto_retriever(d, ISCAS89DatasetRetriever)


def test_iscas89_validate() -> None:
    auto_validate(d, ISCAS89DatasetRetriever, n_jobs=n_jobs)


### KoiosDatasetRetriever ###
def test_koios_retriever() -> None:
    auto_retriever(d, KoiosDatasetRetriever)


def test_koios_validate() -> None:
    auto_validate(d, KoiosDatasetRetriever, n_jobs=n_jobs)


### LGSynth89DatasetRetriever ###
def test_lgsynth89_retriever() -> None:
    auto_retriever(d, LGSynth89DatasetRetriever)


def test_lgsynth89_validate() -> None:
    auto_validate(d, LGSynth89DatasetRetriever, n_jobs=n_jobs)


### LGSynth91DatasetRetriever ###
def test_lgsynth91_retriever() -> None:
    auto_retriever(d, LGSynth91DatasetRetriever)


def test_lgsynth91_validate() -> None:
    auto_validate(d, LGSynth91DatasetRetriever, n_jobs=n_jobs)


### OPDBDatasetRetriever ###
def test_opdb_retriever() -> None:
    auto_retriever(d, OPDBDatasetRetriever)


def test_opdb_validate() -> None:
    auto_validate(d, OPDBDatasetRetriever, n_jobs=n_jobs)


### OpencoresDatasetRetriever ###
def test_opencores_retriever() -> None:
    auto_retriever(d, OpencoresDatasetRetriever)


def test_opencores_validate() -> None:
    auto_validate(d, OpencoresDatasetRetriever, n_jobs=n_jobs)


### VTRDatasetRetriever ###
def test_vtr_retriever() -> None:
    auto_retriever(d, VTRDatasetRetriever)


def test_vtr_validate() -> None:
    auto_validate(d, VTRDatasetRetriever, n_jobs=n_jobs)


### IWLS93DatasetRetriever ###
def test_iwls93_retriever() -> None:
    auto_retriever(d, IWLS93DatasetRetriever)


def test_iwls93_validate() -> None:
    auto_validate(d, IWLS93DatasetRetriever, n_jobs=n_jobs)


### I99TDatasetRetriever ###
def test_i99t_retriever() -> None:
    auto_retriever(d, I99TDatasetRetriever)


def test_i99t_validate() -> None:
    auto_validate(d, I99TDatasetRetriever, n_jobs=n_jobs)


### AddersCVUTDatasetRetriever ###
def test_adderscvut_retriever() -> None:
    auto_retriever(d, AddersCVUTDatasetRetriever)


def test_adderscvut_validate() -> None:
    auto_validate(d, AddersCVUTDatasetRetriever, n_jobs=n_jobs)


### VerilogAddersMongrelgemDatasetRetriever ###
def test_verilog_adders_mongrelgem_retriever() -> None:
    auto_retriever(d, VerilogAddersMongrelgemDatasetRetriever)


def test_verilog_adders_mongrelgem_validate() -> None:
    auto_validate(d, VerilogAddersMongrelgemDatasetRetriever, n_jobs=n_jobs)


### DeepBenchVerilogDatasetRetriever ###
def test_deepbenchverilog_retriever() -> None:
    auto_retriever(d, DeepBenchVerilogDatasetRetriever)


def test_deepbenchverilog_validate() -> None:
    auto_validate(d, DeepBenchVerilogDatasetRetriever, n_jobs=n_jobs)


### MCNC20DatasetRetriever ###
def test_mcnc20_retriever() -> None:
    auto_retriever(d, MCNC20DatasetRetriever)


def test_mcnc20_validate() -> None:
    auto_validate(d, MCNC20DatasetRetriever, n_jobs=n_jobs)


### PolybenchRetriever ###
def test_polybench_retriever() -> None:
    auto_retriever(d, PolybenchRetriever)


def test_polybench_validate() -> None:
    auto_validate(d, PolybenchRetriever, n_jobs=n_jobs)


### RegexFsmVerilogDatasetRetriever ###
def test_regex_fsm_retriever() -> None:
    auto_retriever(d, RegexFsmVerilogDatasetRetriever)


def test_regex_fsm_validate() -> None:
    auto_validate(d, RegexFsmVerilogDatasetRetriever, n_jobs=n_jobs)
