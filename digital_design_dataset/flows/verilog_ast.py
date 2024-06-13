import json
import random
import subprocess
import uuid
from pathlib import Path

import networkx as nx


def generate_node_id(node, rd: random.Random) -> str:
    node_id = str(uuid.UUID(int=rd.getrandbits(128)))
    return node_id


def add_nodes_and_edges(
    g_ast: nx.DiGraph,
    node,
    rd: random.Random,
    parent: str | None = None,
) -> None:
    if node is None:
        return

    node_id = generate_node_id(node, rd)
    node_data_keys = list(node.keys())
    node_data_keys = [k for k in node_data_keys if k != "children"]
    node_data = {k: node[k] for k in node_data_keys}
    g_ast.add_node(node_id, **node_data)  # Add node with attributes
    if parent:
        g_ast.add_edge(parent, node_id, t_edge_type="ast")

    for child in node.get("children", []):
        add_nodes_and_edges(g_ast, child, rd, parent=node_id)


def verilog_ast(
    verilog_file: Path,
    verible_verilog_syntax_bin: str = "verible-verilog-syntax",
) -> nx.DiGraph | None:
    p = subprocess.run(
        [
            verible_verilog_syntax_bin,
            "--export_json",
            "--printtree",
            str(verilog_file.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if p.returncode != 0:
        ast_json = json.loads(p.stdout)
        try:
            ast_json = json.loads(p.stdout)
            if "errors" in list(ast_json.values())[0]:
                # print(p.stdout)
                # print("Verible returned an error")
                return None
        except:  # noqa: E722
            raise RuntimeError(
                f"Verible failed with return code {p.returncode}:\n{p.stderr}",
            )

    ast_json = json.loads(p.stdout)

    if len(ast_json) > 1 or len(ast_json) == 0:
        print("Verible returned more than one AST")

    tree_data = next(iter(ast_json.values()))["tree"]  # get first tree

    rd = random.Random(7)  # noqa: S311

    g_ast = nx.DiGraph()
    add_nodes_and_edges(g_ast, tree_data, rd)

    # check if G is a tree
    if not nx.is_tree(g_ast):
        raise RuntimeError("AST is not a tree")

    # add reverse ast edges
    for u, v, d in g_ast.edges(data=True):
        if d["t_edge_type"] == "ast":
            g_ast.add_edge(v, u, t_edge_type="ast_reverse")

    # add forward and reverse nco edges
    all_nodes = list(g_ast.nodes)
    for i in range(len(all_nodes)):
        if i < len(all_nodes) - 1:
            g_ast.add_edge(all_nodes[i], all_nodes[i + 1], t_edge_type="nco")
        if i > 0:
            g_ast.add_edge(all_nodes[i], all_nodes[i - 1], t_edge_type="nco_reverse")

    # for node in G.nodes(data=True):
    #     print(node)

    # print dot syntax
    # dot = ""
    # dot += "digraph G {\n"
    # for n in G.nodes(data=True):
    #     dot += f"    _{n[0].replace('-', '')} [label=\"{n[1]['tag']}\"];\n"
    # for u, v in G.edges:
    #     dot += f"    _{u.replace('-', '')} -> _{v.replace('-', '')};\n"
    # dot += "}\n"
    # print(dot)

    return g_ast
