import operator
from pathlib import Path

import networkx as nx
from dotenv import dotenv_values

from digital_design_dataset.data_sources.data_retrievers import OpencoresDatasetRetriever
from digital_design_dataset.design_dataset import (
    HARDWARE_DATA_TEXT_EXTENSIONS_SET,
    VERILOG_SOURCE_EXTENSIONS_SET,
    DesignDataset,
)
from digital_design_dataset.flows.decompose import (
    AutoTopModule,
    compute_hierarchy_redundent,
    compute_hierarchy_structured,
    compute_hierarchy_text,
    decompose_design_structured,
    decompose_design_text,
    get_top_nodes,
    simple_synth_check_yosys,
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


def test_decompose_text() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        print(f"Decomposing {d.name} using text approach")
        source_files = sorted(d.rglob("**/*.v"))
        data_decomposed = decompose_design_text(source_files)
        assert data_decomposed


def test_compute_hierarchy_structured() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        print(f"Computing hierarchy for {d.name} using structured approach")
        source_files = sorted(d.rglob("**/*.v"))
        g_hierarchy = compute_hierarchy_structured(source_files)
        assert g_hierarchy


def test_compute_hierarchy_text() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        print(f"Computing hierarchy for {d.name} using text approach")
        source_files = sorted(d.rglob("**/*.v"))
        g_hierarchy = compute_hierarchy_text(source_files)
        assert g_hierarchy


def test_compute_hierarchy_agree() -> None:
    for d in TEST_DESIGNS_SIMPLE:
        source_files = sorted(d.rglob("**/*.v"))
        print(f"Computing hierarchy for {d.name} using structured approach")
        g_hierarchy_structured = compute_hierarchy_structured(source_files)
        print(f"Computing hierarchy for {d.name} using text approach")
        g_hierarchy_text = compute_hierarchy_text(source_files)
        print("Checking hierarchy is equal for both approaches")
        assert nx.is_isomorphic(
            g_hierarchy_structured,
            g_hierarchy_text,
            node_match=operator.eq,
        )


db_path = test_path / "db_test_decompose"
d = DesignDataset(
    db_path,
    overwrite=False,
    gh_token=gh_token,
)


def get_opencores_designs(overwrite: bool = False) -> list[dict]:
    dataset_name = "opencores"
    if overwrite:
        print(f"Overwriting dataset: {dataset_name}")
        designs = d.get_design_metadata_by_dataset_name(dataset_name)
        for design in designs:
            d.delete_design(design["design_name"])
        OpencoresDatasetRetriever(d).get_dataset()
        designs = d.get_design_metadata_by_dataset_name(dataset_name)
        designs = sorted(designs, key=operator.itemgetter("design_name"))
    else:
        designs = d.get_design_metadata_by_dataset_name(dataset_name)
        designs = sorted(designs, key=operator.itemgetter("design_name"))
        if not designs:
            OpencoresDatasetRetriever(d).get_dataset()
            designs = d.get_design_metadata_by_dataset_name(dataset_name)
            designs = sorted(designs, key=operator.itemgetter("design_name"))
    return designs


def test_decompose_structured__opencores() -> None:
    designs = get_opencores_designs()
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        print(
            f"{i + 1}/{num_designs} Decomposing {design_name} using structured approach",
        )
        data_decomposed = decompose_design_structured(verilog_sources_fps)
        print(len(data_decomposed))
        assert data_decomposed


def test_decompose_text__opencores() -> None:
    designs = get_opencores_designs()
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        data_files = [f for f in sources_fps if f.suffix in HARDWARE_DATA_TEXT_EXTENSIONS_SET]
        if data_files == []:
            data_files = None

        print(
            f"{i + 1}/{num_designs} Decomposing {design_name} using text approach",
        )
        data_decomposed = decompose_design_text(verilog_sources_fps, data_files)
        print(len(data_decomposed))
        assert data_decomposed


def test_compute_hierarchy_structured__opencores() -> None:
    designs = get_opencores_designs()
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        print(
            f"{i + 1}/{num_designs} Computing hierarchy for {design_name} using text approach",
        )
        g_hierarchy = compute_hierarchy_structured(verilog_sources_fps)
        assert g_hierarchy


def test_compute_hierarchy_text__opencores() -> None:
    designs = get_opencores_designs()
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        print(
            f"{i + 1}/{num_designs} Computing hierarchy for {design_name} using text approach",
        )
        g_hierarchy = compute_hierarchy_structured(verilog_sources_fps)
        assert g_hierarchy


def test_compute_hierarchy_agree__opencores() -> None:
    designs = get_opencores_designs()
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        print(
            f"{i + 1}/{num_designs} Computing hierarchy for {design_name} using structured approach",
        )
        g_hierarchy_structured = compute_hierarchy_structured(verilog_sources_fps)
        print(
            f"{i + 1}/{num_designs} Computing hierarchy for {design_name} using text approach",
        )
        g_hierarchy_text = compute_hierarchy_text(verilog_sources_fps)
        print(f"{i + 1}/{num_designs} Checking hierarchy is equal for both approaches")
        assert nx.is_isomorphic(
            g_hierarchy_structured,
            g_hierarchy_text,
            node_match=operator.eq,
        )


def test_single_top__opencores():
    designs = get_opencores_designs(overwrite=True)
    num_designs = len(designs)
    for i, design in enumerate(designs):
        design_name = design["design_name"]
        design_dir = d.designs_dir / design_name
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]
        print(
            f"{i + 1}/{num_designs} Computing hierarchy for {design_name} using text approach",
        )

        g = compute_hierarchy_redundent(verilog_sources_fps)
        top_nodes = get_top_nodes(g)
        auto_top_helper = AutoTopModule(g)

        db = auto_top_helper.scores_huristic
        db_sorted = sorted(db.items(), key=operator.itemgetter(1), reverse=True)
        auto_top = max(db.items(), key=operator.itemgetter(1))[1]

        db_n_nodes = auto_top_helper.scores_n_nodes

        if len(top_nodes) == 1:
            top_node = top_nodes[0]
        else:
            score_diff = abs(db_sorted[0][1] - db_sorted[1][1])

            if score_diff > 0.5:
                top_node = db_sorted[0][0]
                print(f"Computed based on differential: {db_sorted=}")
            elif len(set(db_n_nodes.values())) > 1:
                top_nodes_filtered = [node for node, score in db_n_nodes.items() if score > 0]
                print(f"Filtered: {top_nodes_filtered=}")
                if len(top_nodes_filtered) == 1:
                    top_node = top_nodes_filtered[0]
                    print(f"Computed based on singleton filter: {db_n_nodes=}")
                else:
                    top_node = None
            else:
                top_node = None

        dot_fp = design_dir / "h.dot"
        dot_fp.write_text(nx.nx_agraph.to_agraph(g).string())
        print(f"Saved hierarchy to {dot_fp}")

        if top_node is None:
            print(nx.nx_agraph.to_agraph(g).string())
            print(f"Top nodes: {top_nodes}")
            print(f"Top nodes score: {db_sorted=}")
            print(f"Top nodes n_nodes: {db_n_nodes=}")
            print(f"Auto top: {auto_top}")
            raise ValueError(f"Could not find top module for design {design_name}, candidates: {top_nodes}")

        print(f"Top module: {top_node}")

        assert simple_synth_check_yosys(
            {fp.name: fp.read_text() for fp in verilog_sources_fps},
            top_node,
        )
