from pathlib import Path

from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import (
    DataRetriever,
    EPFLDatasetRetriever,
    HW2VecDatasetRetriever,
    ISCAS85DatasetRetriever,
    ISCAS89DatasetRetriever,
    KoiosDatasetRetriever,
    LGSynth89DatasetRetriever,
    LGSynth91DatasetRetriever,
    OPDBDatasetRetriever,
    OpencoresDatasetRetriever,
    VTRDatasetRetriever,
    IWLS93DatasetRetriever,
    I99TDatasetRetriever,
    AddersCVUTDatasetRetriever,
    MCNC20DatasetRetriever,
    DeepBenchVerilogDatasetRetriever,
    RegexFsmVerilogDatasetRetriever,
    XACTDatasetRetriever,
    EspressoPLADatasetRetriever,
    FPGAMicroBenchmarksDatasetRetriever
)
from digital_design_dataset.data_sources.hls_data import (
    PolybenchRetriever
)
from digital_design_dataset.design_dataset import (
    DesignDataset,
)

DIR_CURRENT = Path(__file__).parent

env_config = dotenv_values(DIR_CURRENT / ".env")
gh_token = None
if "GITHUB_TOKEN" in env_config:
    gh_token = env_config["GITHUB_TOKEN"]

test_db_dir = DIR_CURRENT / "test_dataset_v2"
d = DesignDataset(
    test_db_dir,
    overwrite=True,
    gh_token=gh_token,
)

retrivers = [    EPFLDatasetRetriever,
    HW2VecDatasetRetriever,
    ISCAS85DatasetRetriever,
    ISCAS89DatasetRetriever,
    KoiosDatasetRetriever,
    LGSynth89DatasetRetriever,
    LGSynth91DatasetRetriever,
    OPDBDatasetRetriever,
    OpencoresDatasetRetriever,
    VTRDatasetRetriever,
    IWLS93DatasetRetriever,
    I99TDatasetRetriever,
    AddersCVUTDatasetRetriever,
    MCNC20DatasetRetriever,
    DeepBenchVerilogDatasetRetriever,
    RegexFsmVerilogDatasetRetriever,
    XACTDatasetRetriever,
    EspressoPLADatasetRetriever,
    FPGAMicroBenchmarksDatasetRetriever,
    PolybenchRetriever,
]

for retriver_cls in retrivers:
    print(f"Retrieving dataset: {retriver_cls.__name__}")
    retriver: DataRetriever = retriver_cls(d)
    retriver.get_dataset()