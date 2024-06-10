from pathlib import Path
from timeit import default_timer as timer

import pandas as pd
import tqdm
from rich import print

from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.models.verilog_tokenizer import (
    build_verilog_tokenizer,
    load_tokenizer,
    save_tokenizer,
)

if __name__ == "__main__":
    current_script_dir = Path(__file__).parent
    test_db_dir = current_script_dir / "test_dataset"

    test_dataset = DesignDataset(test_db_dir)

    tokenizer_dir = current_script_dir / "tokenizers"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_fp = current_script_dir / "tokenizers" / "verilog_tokenizer.json"

    if tokenizer_fp.exists():
        tokenizer = load_tokenizer(tokenizer_fp)
    else:
        tokenizer = build_verilog_tokenizer(test_dataset.dir)
        save_tokenizer(tokenizer, tokenizer_fp)

    design_0 = test_dataset.get_all_verilog_files()[0]
    design_0_text_100 = design_0.read_text()[:100]

    print("design_0_text_100")
    print("-----------------")
    print(design_0_text_100)
    print()

    print("tokenizer.encode(design_0_text_100)")
    print("-----------------------------------")
    print(tokenizer.encode(design_0_text_100).ids)
    print()

    print("tokenizer.decode(tokenizer.encode(design_0_text_100))")
    print("-----------------------------------------------------")
    print(tokenizer.decode(tokenizer.encode(design_0_text_100).ids))
    print()

    encode_data: list[dict] = []
    for design in tqdm.tqdm(test_dataset.get_all_verilog_files()):
        fp_str = str(design)
        file_text = design.read_text()
        t_start = timer()
        seq = tokenizer.encode(file_text)
        t_end = timer()
        dt = t_end - t_start
        seq_len = len(seq.ids)
        data = {
            "fp": fp_str,
            "seq_len": seq_len,
            "encode_time": dt,
        }
        encode_data.append(data)

    # write to csv file
    df = pd.DataFrame(encode_data)
    df.to_csv(current_script_dir / "encode_data.csv", index=False)
