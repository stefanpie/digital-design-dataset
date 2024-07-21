import operator
from pathlib import Path
from pprint import pp

from dotenv import dotenv_values

from digital_design_dataset.dataset.datasets import OpencoresDatasetRetriever
from digital_design_dataset.design_dataset import (
    HARDWARE_DATA_TEXT_EXTENSIONS,
    HARDWARE_DATA_TEXT_EXTENSIONS_SET,
    VERILOG_SOURCE_EXTENSIONS_SET,
    DesignDataset,
)
from digital_design_dataset.flows.decompose import (
    decompose_design_structured,
    decompose_design_text,
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

# load n_jobs
if "N_JOBS" not in env_config:
    raise ValueError("N_JOBS not defined in .env file")
n_jobs_val = env_config["N_JOBS"]
if not n_jobs_val:
    raise ValueError("N_JOBS not defined in .env file")
try:
    n_jobs = int(n_jobs_val)
except ValueError:
    raise ValueError("N_JOBS must be an integer")
if n_jobs < 1:
    raise ValueError("N_JOBS must be greater than 0")


DIR_TEST_DESIGNS = DIR_CURRENT / "test_designs"
TEST_DESIGNS_SIMPLE = [
    DIR_TEST_DESIGNS / "hdesign_0",
    DIR_TEST_DESIGNS / "hdesign_1",
    DIR_TEST_DESIGNS / "hdesign_2",
    DIR_TEST_DESIGNS / "hdesign_3",
]


def test_decompose_structured() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        print(f"Decomposing {d.name} using structured approach")
        source_files = sorted(d.rglob("**/*.v"))
        data_decomposed = decompose_design_structured(source_files)
        assert data_decomposed
        # pp(data_decomposed)


def test_decompose_text() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        print(f"Decomposing {d.name} using text approach")
        source_files = sorted(d.rglob("**/*.v"))
        data_decomposed = decompose_design_text(source_files)
        assert data_decomposed
        pp(data_decomposed)


# load design dataset


db_path = test_path / "db"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)


def rank_designs_by_size(d: DesignDataset, designs: list[dict]) -> list[dict]:
    sizes = []
    for design in designs:
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]
        size = sum(len(f.read_text()) for f in verilog_sources_fps)
        sizes.append((design, size))
    # small to large
    sizes = sorted(sizes, key=operator.itemgetter(1))
    designs_sorted = [design for design, _ in sizes]
    return designs_sorted


def get_opencores_designs() -> list[dict]:
    # setup test designs in the dataset
    db_path = test_path / "db"
    d = DesignDataset(
        db_path,
        overwrite=False,
        gh_token=gh_token,
    )
    dataset_name = "opencores"
    designs = d.get_design_metadata_by_dataset_name(dataset_name)
    designs = sorted(designs, key=operator.itemgetter("design_name"))
    if not designs:
        OpencoresDatasetRetriever(d).get_dataset()
        designs = d.get_design_metadata_by_dataset_name(dataset_name)

    return designs


def test_decompose_structured__opencores() -> None:
    designs = get_opencores_designs()
    designs = rank_designs_by_size(d, designs)
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]
        print(
            f"{i + 1}/{num_designs} Decomposing {design_name} using structured approach",
        )
        data_decomposed = decompose_design_structured(verilog_sources_fps)
        print(len(data_decomposed))
        assert data_decomposed


def test_decompose_text__opencores() -> None:
    designs = get_opencores_designs()
    designs = rank_designs_by_size(d, designs)
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]
        data_files = [
            f for f in sources_fps if f.suffix in HARDWARE_DATA_TEXT_EXTENSIONS_SET
        ]
        if data_files == []:
            data_files = None

        print(
            f"{i + 1}/{num_designs} Decomposing {design_name} using text approach",
        )
        data_decomposed = decompose_design_text(verilog_sources_fps, data_files)
        print(len(data_decomposed))
        assert data_decomposed


edge_case_designs_structured = [
    "opencores__yadmc",
]


def test_decompose_structured__edge_cases() -> None:
    designs = get_opencores_designs()

    designs = sorted(
        filter(lambda d: d["design_name"] in edge_case_designs_structured, designs),
        key=operator.itemgetter("design_name"),
    )

    for design in designs:
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]

        print(f"Decomposing {design_name} using structured approach")
        data_decomposed = decompose_design_structured(verilog_sources_fps)
        print(len(data_decomposed))
        assert data_decomposed


edge_case_designs_text = [
    "opencores__cavlc",
]


def test_decompose_text__edge_cases() -> None:
    designs = get_opencores_designs()

    designs = sorted(
        filter(lambda d: d["design_name"] in edge_case_designs_text, designs),
        key=operator.itemgetter("design_name"),
    )

    pp(designs)

    for design in designs:
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]

        print(f"Decomposing {design_name} using text approach")
        data_decomposed = decompose_design_text(verilog_sources_fps)
        print(len(data_decomposed))
        assert data_decomposed
