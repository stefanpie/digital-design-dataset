import json
from pathlib import Path
from pprint import pp

import pandas as pd
import tiktoken
from dotenv import dotenv_values

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
except ValueError as e:
    raise ValueError("N_JOBS must be an integer") from e
if n_jobs < 1:
    raise ValueError("N_JOBS must be greater than 0")


encoders = {
    "cl100k_base": tiktoken.get_encoding("cl100k_base"),
    "o200k_base": tiktoken.get_encoding("o200k_base"),
}


print("Loading dataset")
df = pd.read_csv(
    "hf://datasets/shailja/Verilog_GitHub/Verilog_bigquery_GitHub.csv",
)

print("Processing dataset")
token_counts = dict.fromkeys(encoders, 0)
for encoder_name, encoder in encoders.items():
    print(f"Processing {encoder_name}")
    tokens = encoder.encode_batch(df["text"].tolist(), num_threads=n_jobs)
    token_lengths = [len(t) for t in tokens]
    token_counts[encoder_name] += sum(token_lengths)

pp(token_counts)
data_fp = data_dir / "token_counts_verigen.json"
data_fp.write_text(json.dumps(token_counts, indent=4))
