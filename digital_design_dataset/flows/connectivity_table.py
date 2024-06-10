from io import StringIO

import networkx as nx
import pandas as pd


def parse_connectivity_table(connectivity_table: str) -> nx.DiGraph:
    df = pd.read_csv(
        StringIO(connectivity_table),
        sep="\t",
        header=None,
        names=[
            "module_name",
            "cell_name",
            "cell_type",
            "cell_port",
            "direction",
            "signal",
        ],
    )

    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_node(
            row["cell_name"],
            cell_type=row["cell_type"],
            module_name=row["module_name"],
            node_type="cell",
        )
    for _, row in df.iterrows():
        G.add_node(row["signal"], node_type="signal")
    for _, row in df.iterrows():
        direction = row["direction"]
        if direction == "in" or direction == "pi":
            G.add_edge(
                row["signal"],
                row["cell_name"],
                cell_port=row["cell_port"],
                direction=row["direction"],
            )
        elif direction == "out" or direction == "po":
            G.add_edge(
                row["cell_name"],
                row["signal"],
                cell_port=row["cell_port"],
                direction=row["direction"],
            )
        elif direction == "inout" or direction == "pio":
            G.add_edge(
                row["signal"],
                row["cell_name"],
                cell_port=row["cell_port"],
                direction=row["direction"],
            )
            G.add_edge(
                row["cell_name"],
                row["signal"],
                cell_port=row["cell_port"],
                direction=row["direction"],
            )
        else:
            raise ValueError(f"Unknown direction: {direction}")

    return G
