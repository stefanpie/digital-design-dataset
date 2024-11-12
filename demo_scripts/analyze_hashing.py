import hashlib
import multiprocessing
import re
from pathlib import Path

import pandas as pd
import tqdm
from dotenv import dotenv_values

from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.flows import ModuleInfoFlow
from digital_design_dataset.logger import build_logger

logger = build_logger("analyze_hashing")

current_script_dir = Path(__file__).parent

output_dir = current_script_dir / "output"
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

# run the module_info flow on all designs
f_module = ModuleInfoFlow(test_dataset)


def run_single(design: dict) -> None:
    logger.info(f"{design['design_name']}: Running {f_module.__class__.__name__}")
    f_module.build_flow_single(design)


all_designs = test_dataset.index
pool = multiprocessing.Pool(n_jobs)
pool.map(run_single, all_designs, chunksize=1)
pool.close()
pool.join()


corpus_fps = []
design_names = []
dataset_names = []
n_modules = []
for design in test_dataset.index:
    num_modules_fp = test_dataset.designs_dir / design["design_name"] / "flows" / "module_count" / "num_modules.txt"
    n_modules.append(int(num_modules_fp.read_text().strip()))
    source_files = test_dataset.get_design_source_files(design["design_name"])
    for fp in source_files:
        corpus_fps.append(fp)
        design_names.append(design["design_name"])
        dataset_names.append(design["dataset_name"])

print("Number of modules:")
print(sum(n_modules))

RE_C_COMMENT = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE,
)


def comment_replacer(match):
    s = match.group(0)
    if s.startswith("/"):
        return " "  # note: a space and not an empty string
    return s


def comment_remover(text):
    return re.sub(RE_C_COMMENT, comment_replacer, text)


RE_MODULE = re.compile(r"module[ \t]*([^\s]*)[ \t]*(?:\(|#)(?:.*|\s)*?endmodule")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_modules_from_file(fp: Path, design_name: str, dataset_name: str):
    source = fp.read_text()
    source_no_comments = comment_remover(source)

    data = []

    module_matches = re.finditer(RE_MODULE, source_no_comments)
    for m in module_matches:
        module_name = m.group(1)
        module_text = m.group(0)
        mpdule_text_no_whitespace = re.sub(r"\s+", "", module_text)
        module_hash = hash_text(mpdule_text_no_whitespace)

        data.append({
            "module_hash": module_hash,
            "module_name": module_name,
            "design_name": design_name,
            "dataset_name": dataset_name,
        })

    return data


data_single = []
for fp, design_name, dataset_name in tqdm.tqdm(
    zip(corpus_fps, design_names, dataset_names, strict=False),
    total=len(corpus_fps),
):
    data_single.extend(hash_modules_from_file(fp, design_name, dataset_name))

df = pd.DataFrame(data_single)
df_grouped = df.groupby("module_hash").agg(count=("module_hash", "count")).rename(columns={"count": "unique_count"})
df = df.merge(df_grouped, on="module_hash")
df = df.sort_values(
    ["unique_count", "module_hash", "module_name", "design_name", "dataset_name"],
    ascending=False,
)

output_dir.mkdir(exist_ok=True, parents=True)
df.to_csv(output_dir / "module_hashes.csv", index=False)

# pint the number of unique hashes
print("Number of unique module hashes:")
print(df["module_hash"].nunique())

print("Number of unique designs:")
print(df["design_name"].nunique())


# count lines of code
def count_lines_of_code(text: str) -> int:
    lines = text.split("\n")
    lines_not_empty = [line for line in lines if line.strip() != ""]
    return len(lines_not_empty)


def total_lines_of_code(corpus_fps):
    total_lines = 0
    for fp in corpus_fps:
        total_lines += count_lines_of_code(fp.read_text())
    return total_lines


total_lines = total_lines_of_code(corpus_fps)
print("Total lines of code:")
print(total_lines)


# count the file sizes
def total_file_sizes(corpus_fps):
    total_size = 0
    for fp in corpus_fps:
        total_size += fp.stat().st_size
    return total_size


total_size = total_file_sizes(corpus_fps)
print("Total file size:")
print(total_size)
