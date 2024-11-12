from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import tiktoken
from dotenv import dotenv_values
from joblib import Parallel, delayed

from digital_design_dataset.design_dataset import DesignDataset

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


corpus_fps = []
design_names = []
dataset_names = []
for design in test_dataset.index:
    source_files = test_dataset.get_design_source_files(design["design_name"])
    for fp in source_files:
        corpus_fps.append(fp)
        design_names.append(design["design_name"])
        dataset_names.append(design["dataset_name"])

encoders = {
    "cl100k_base": tiktoken.get_encoding("cl100k_base"),
    "o200k_base": tiktoken.get_encoding("o200k_base"),
}

token_counts = {e: [] for e in encoders}


def compute_tokens(
    fp: Path,
    design_name: str,
    dataset_name: str,
    encoder: tiktoken.Encoding,
) -> int:
    print(f"Processing: {encoder.name} - {dataset_name} - {design_name} - {fp.name}")
    text = fp.read_text()
    tokens = encoder.encode(text)
    num_tokens = len(tokens)
    return num_tokens


for e in encoders:
    all_data = zip(corpus_fps, design_names, dataset_names, strict=False)

    # use joblib
    token_counts[e] = Parallel(n_jobs=n_jobs, backend="threading")(  # type: ignore
        delayed(compute_tokens)(fp, design_name, dataset_name, encoders[e])
        for fp, design_name, dataset_name in all_data
    )

df_tokens = pd.DataFrame(
    columns=["dataset_name", "design_name", "file_name", "tokenizer", "num_tokens"],
)
for e in encoders:
    df_single = pd.DataFrame(
        {
            "dataset_name": dataset_names,
            "design_name": design_names,
            "file_name": [fp.name for fp in corpus_fps],
            "tokenizer": e,
            "num_tokens": token_counts[e],
        },
    )
    df_tokens = pd.concat([df_tokens, df_single], axis=0)

df_tokens.to_csv(data_dir / "token_count.csv", index=False)

# make a seaborm bar plot of sum of differnt token counts, the x axis is the dataset,
# adn the y axis is the number of tokens log scaled stating at 10,000
# plot only the cl100k_base tokenizer
# also make sure the datasets are sorted from least to most tokens on the x axis

tokenizer_to_plot = "cl100k_base"

df_plot = df_tokens.copy()
df_plot = df_plot[df_plot["tokenizer"] == tokenizer_to_plot]
df_plot = df_plot.groupby("dataset_name").sum()
df_plot = df_plot.sort_values("num_tokens")

# make a seaborn bar plot of sum of different token counts, the x axis is the dataset,
# adn the y axis is the number of tokens log scaled stating at 10,000
# plot only the cl100k_base tokenizer
# also make sure the datasets are sorted from least to most tokens on the x axis
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    x=df_plot.index,
    y=df_plot["num_tokens"],
    ax=ax,
)
ax.set_yscale("log")
ax.set_yticks([1e4, 1e5, 1e6, 1e7, 1e8, 1e9])

# rotate x labels
for tick in ax.get_xticklabels():
    tick.set_rotation(90)

ax.set_ylabel("Number of Tokens")
ax.set_xlabel("Dataset Name")

ax.set_title(f"LLM Token Count by Dataset (tokenizer: {tokenizer_to_plot})")

fig.tight_layout()
fig.savefig(figure_dir / "fig_token_count.png", dpi=300)


# make another plot that is a line plot of the number of tokens per each design in the dataset
# in this case each index on the x axis is a design name, and the y axis is the number of tokens

df_plot = df_tokens.copy()
df_plot = df_plot[df_plot["tokenizer"] == tokenizer_to_plot]
df_plot = df_plot.groupby("design_name").sum()
df_plot = df_plot.sort_values("num_tokens")

fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(
    data=df_plot,
    x="num_tokens",
    bins=100,
    ax=ax,
    log_scale=(True, False),
)

ax.set_ylabel("Count")
ax.set_xlabel("Number of Tokens")

ax.set_title(f"LLM Token Count Distribution by Design (tokenizer: {tokenizer_to_plot})")

fig.tight_layout()
fig.savefig(figure_dir / "fig_token_count_dist.png", dpi=300)
