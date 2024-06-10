from pathlib import Path

from rich.pretty import pprint as pp

from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.yosys_synth_xilinx import yosys_synth_xilinx

# import networkx as nx
# import matplotlib.pyplot as plt


if __name__ == "__main__":
    current_script_dir = Path(__file__).parent
    test_db_dir = current_script_dir / "test_dataset"
    test_dataset = DesignDataset(test_db_dir)

    design_0 = test_dataset.get_all_verilog_files()[0]

    netlist = yosys_synth_xilinx(design_0)

    pp(netlist)
