from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.yosys_aig import yosys_aig

if __name__ == "__main__":
    current_script_dir = Path(__file__).parent
    test_db_dir = current_script_dir / "test_dataset_v2"
    test_dataset = DesignDataset(test_db_dir)

    design_sources = test_dataset.get_design_source_files("adder4bit_1")

    aig, json_data = yosys_aig(design_sources)
    print(json_data)

    colors = [
        "blue" if data["node_type"] == "cell" else "black"
        for _, data in aig.nodes(data=True)
    ]
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    nx.draw_networkx(aig, ax=ax, with_labels=False, node_size=10, node_color=colors)

    plt.tight_layout()
    plt.savefig(Path(__file__).parent / "figures" / "test_verilog_aig.png", dpi=300)
