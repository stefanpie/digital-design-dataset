from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dotenv import dotenv_values
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

from digital_design_dataset.design_dataset import DesignDataset

current_script_dir = Path(__file__).parent

figure_dir = current_script_dir / "figures"

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


print(f"len(corpus_fps): {len(corpus_fps)}")
vectorizer = TfidfVectorizer(analyzer="word", max_features=1024, ngram_range=(1, 3))
X = vectorizer.fit_transform([fp.read_text() for fp in corpus_fps])
X = np.asarray(X.todense())  # type: ignore
print(f"X.shape: {X.shape}")

transforms = [
    ("PCA", PCA(n_components=2)),
    ("SVD", TruncatedSVD(n_components=2)),
    ("TSNE", TSNE(n_components=2, perplexity=50)),
    # (
    #     "PACMAP",
    #     pacmap.PaCMAP(
    #         n_components=2,
    #         n_neighbors=10,
    #         MN_ratio=0.5,
    #         FP_ratio=5,
    #     ),
    # ),
]

x_out_values = []
y_out_values = []
for name, transform in transforms:
    print(f"Running {name}")
    X_reduced = transform.fit_transform(X)
    x_out_values.append(X_reduced[:, 0])
    y_out_values.append(X_reduced[:, 1])


print("Plotting")
n_panels = len(transforms)
fig, axes = plt.subplots(1, n_panels, figsize=(10 * n_panels, 10))
unique_datasets = list(set(dataset_names))
colors = plt.cm.tab20(np.linspace(0, 1, len(unique_datasets)))  # type: ignore

for i, dataset in enumerate(unique_datasets):
    indices = [j for j, x in enumerate(dataset_names) if x == dataset]
    for j, (name, _) in enumerate(transforms):
        axes[j].scatter(
            x_out_values[j][indices],
            y_out_values[j][indices],
            c=colors[i],
            label=dataset,
        )
        axes[j].set_title(name)
        axes[j].legend()
plt.tight_layout()
plt.savefig(figure_dir / "test_verilog_source_vis.png", dpi=300)
