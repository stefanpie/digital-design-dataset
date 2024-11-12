from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from digital_design_dataset.design_dataset import DesignDataset
from digital_design_dataset.flows.verilog_ast import verilog_ast

if __name__ == "__main__":
    current_script_dir = Path(__file__).parent
    test_db_dir = current_script_dir / "test_dataset_v2"

    test_dataset = DesignDataset(test_db_dir)

    design_0 = test_dataset.get_design_source_files("adder4bit_1")[0]

    ast_tree = verilog_ast(design_0)
    if ast_tree is None:
        raise ValueError("AST tree is None")
    nx.nx_agraph.write_dot(
        ast_tree,
        current_script_dir / "figures" / "verilog_ast_tree.dot",
    )

    fig, ax = plt.subplots(1, 2, figsize=(14, 8))
    edge_colors = {"ast": "blue", "nco": "red"}
    pos = nx.nx_agraph.graphviz_layout(ast_tree, prog="twopi")
    nx.draw_networkx_nodes(ast_tree, pos, ax=ax[0], node_size=50)
    nx.draw_networkx_nodes(ast_tree, pos, ax=ax[1], node_size=50)
    edges_ast = [edge for edge in ast_tree.edges(data=True) if edge[2]["t_edge_type"] == "ast"]
    edges_nco = [edge for edge in ast_tree.edges(data=True) if edge[2]["t_edge_type"] == "nco"]
    nx.draw_networkx_edges(ast_tree, pos, edgelist=edges_ast, ax=ax[0], node_size=50)
    nx.draw_networkx_edges(
        ast_tree,
        pos,
        edgelist=edges_nco,
        ax=ax[1],
        node_size=50,
        style="dashed",
        connectionstyle="arc3,rad=0.1",
    )
    plt.tight_layout()
    figures_fp = current_script_dir / "figures"
    if not figures_fp.exists():
        figures_fp.mkdir(parents=True, exist_ok=True)
    plt.savefig(current_script_dir / "figures" / "verilog_ast_tree.png")
