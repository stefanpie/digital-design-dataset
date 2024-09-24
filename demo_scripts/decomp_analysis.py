import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

import joblib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import tqdm
from dotenv import dotenv_values
from joblib import Parallel, delayed

from digital_design_dataset.design_dataset import VERILOG_SOURCE_EXTENSIONS, DesignDataset
from digital_design_dataset.flows.decompose import compute_hierarchy_structured, extract_unique_subgraphs

current_script_dir = Path(__file__).parent

figure_dir = current_script_dir / "figures"
data_dir = current_script_dir / "output"

env_config = dotenv_values(current_script_dir / ".env")

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

# load dataset path
if "DB_PATH" in env_config:
    db_path_val = env_config["DB_PATH"]
    if not db_path_val:
        raise ValueError("DB_PATH not defined in .env file")
    try:
        db_path = Path(db_path_val)
    except Exception as e:
        raise ValueError(f"An error occurred while processing DB_PATH: {e!s}")


test_dataset = DesignDataset(
    db_path,
    overwrite=False,
)

opencores_designs = test_dataset.get_design_metadata_by_dataset_name("opencores")


def process_design(design):
    design_name = design["design_name"]
    design_dir = test_dataset.designs_dir / design_name

    data = {}
    data["design_name"] = design_name

    design_sources = sorted((design_dir / "sources").glob("*"))
    # filter to ensure only verilog files are considered
    design_sources = [source for source in design_sources if source.suffix in VERILOG_SOURCE_EXTENSIONS]
    design_aux = sorted((design_dir / "aux_files").glob("*"))

    g_structured = compute_hierarchy_structured(design_sources)
    all_module_list = list(nx.lexicographical_topological_sort(g_structured))
    sub_designs = extract_unique_subgraphs(g_structured, all_module_list)

    num_sub_designs = len(sub_designs)
    data["num_sub_designs"] = num_sub_designs

    return data


data_decomp: list = Parallel(n_jobs=n_jobs)(delayed(process_design)(design) for design in tqdm.tqdm(opencores_designs))

num_original_designs = len(opencores_designs)
num_sub_designs = sum([data["num_sub_designs"] for data in data_decomp])


print(f"Original designs: {num_original_designs}")
print(f"Sub-designs: {num_sub_designs}")

ratio = num_sub_designs / num_original_designs
print(f"Expansion Factor: {ratio}")

data = {
    "opencores": {
        "original_designs": num_original_designs,
        "sub_designs": num_sub_designs,
        "expansion_factor": ratio,
    },
}

data_fp = data_dir / "decomp_analysis.json"
data_fp.write_text(json.dumps(data, indent=4))
