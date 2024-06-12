from pathlib import Path

from dotenv import dotenv_values

from digital_design_dataset.dataset.datasets import (
    AddersCVUTDatasetRetriever,
    EPFLDatasetRetriever,
    HW2VecDatasetRetriever,
    I99TDatasetRetriever,
    ISCAS85DatasetRetriever,
    ISCAS89DatasetRetriever,
    IWLS93DatasetRetriever,
    KoiosDatasetRetriever,
    LGSynth89DatasetRetriever,
    LGSynth91DatasetRetriever,
    OPDBDatasetRetriever,
    OpencoresDatasetRetriever,
    VTRDatasetRetriever,
)
from digital_design_dataset.design_dataset import (
    DesignDataset,
)

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


# load design dataset
db_path = test_path / "db"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)


def remove_existing_dataset_designs(d: DesignDataset, retriever_name: str) -> None:
    designs = d.get_design_metadata_by_dataset_name(retriever_name)
    for design in designs:
        d.delete_design(design["design_name"])


def test_epfl_dataset_retriever() -> None:
    r = EPFLDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_hw2vec_dataset_retriever() -> None:
    r = HW2VecDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_iscas85_dataset_retriever() -> None:
    r = ISCAS85DatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_iscas89_dataset_retriever() -> None:
    r = ISCAS89DatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_koios_dataset_retriever() -> None:
    r = KoiosDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_lgsynth89_dataset_retriever() -> None:
    r = LGSynth89DatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_lgsynth91_dataset_retriever() -> None:
    r = LGSynth91DatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_opdb_dataset_retriever() -> None:
    r = OPDBDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_opencores_dataset_retriever() -> None:
    r = OpencoresDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_vtr_dataset_retriever() -> None:
    r = VTRDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_iwls93_dataset_retriever() -> None:
    r = IWLS93DatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


# I99TDatasetRetriever
def test_i99t_dataset_retriever() -> None:
    r = I99TDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()


def test_adders_cvut_dataset_retriever() -> None:
    r = AddersCVUTDatasetRetriever(d)
    remove_existing_dataset_designs(d, r.__class__.dataset_name)
    r.get_dataset()
