import json
import subprocess
import tempfile
from pathlib import Path

import networkx as nx

from digital_design_dataset.flows.connectivity_table import parse_connectivity_table


def yosys_aig(
    verilog_files: list[Path],
    yosys_bin: str = "yosys",
) -> tuple[nx.DiGraph, dict, str, dict]:
    connectivity_table_temp_file = tempfile.NamedTemporaryFile(suffix=".txt")
    json_temp_file = tempfile.NamedTemporaryFile(suffix=".json")
    stat_temp_file = tempfile.NamedTemporaryFile(suffix=".stat")
    stat_json_temp_file = tempfile.NamedTemporaryFile(suffix=".stat.json")

    script = ""
    for verilog_file in verilog_files:
        # script += f"read_verilog -nomem2reg {verilog_file};\n"
        script += f"read_verilog {verilog_file};\n"
    script += "hierarchy -check -auto-top;\n"
    script += "synth -run begin:fine;\n"
    script += "dffunmap;\n"
    script += "aigmap;\n"
    script += f"write_table {connectivity_table_temp_file.name};\n"
    script += f"write_json {json_temp_file.name};\n"
    script += f"tee -o {stat_temp_file.name} stat;\n"
    script += f"tee -o {stat_json_temp_file.name} stat -json;\n"

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        check=False,
    )
    if p.returncode != 0:
        print(script)
        print(p.stdout.decode())
        print(p.stderr.decode())
        raise RuntimeError("Yosys failed with return code: " + str(p.returncode))

    connectivity_table_raw = connectivity_table_temp_file.read().decode().strip()
    connectivity_table_temp_file.close()
    graph = parse_connectivity_table(connectivity_table_raw)

    json_raw = json_temp_file.read().decode().strip()
    json_temp_file.close()
    json_data = json.loads(json_raw)

    stat_raw = stat_temp_file.read().decode().strip()
    stat_temp_file.close()

    stat_json_raw = stat_json_temp_file.read().decode().strip()
    stat_json_temp_file.close()
    stat_json_data = json.loads(stat_json_raw)

    return graph, json_data, stat_raw, stat_json_data


#
# Function to take raw AIG file and convert it into a graph
#
def raw_aig_to_tree(raw_aig: str) -> nx.DiGraph:
    # Give myself some extra info if I need to debug
    debug = True

    # Create the graph to fill up and return
    aig_graph = nx.MultiDiGraph()

    # Do I need this step for AIG? TODO
    # T.add_node("root", type="AST_ROOT")

    # Create a list of the lines of the raw aig and eliminate any blank lines.
    lines = raw_aig.splitlines()
    lines = [line for line in lines if line.strip() != ""]

    # Keep track of any errors that we catch
    errors = 0

    # Steps:
    # 1. Parse header to get counts of all the different parts of the design.
    # 2. Find the header-indicated number of inputs and add them to the node list with flag for input
    # 3. Find header-indicated number of latches and add them to list of nodes
    # 4. Find head-indicated number of outputs and add them to the node list with flag for output
    # 5. Find head-indicated number of ANDs and add them to node list as ANDs
    # 6. Revisit latches and add their edges, connecting the right nodes
    # 7. Revisit ANDs and add their edges, connecting the right nodes.

    # Note:
    # I need to actively check for odd numbers. If a number is odd, it means its the inverse of -1 even number.

    # All the above dependent on how the MultiDiGraph objects work.
    # Inputs and outputs will be considered nodes.
    # I want to make sure nodes are properly created with their type before I add edges; I'll visit AND and LATCH lines twice to this end
    # Nodes will be added as their index on the AIG, since Nodes are "named" in MultiDiGraphs.
    # Edges will be allowed to auto-assign their inherent "key" value, but I will give them an "index" value
    #   that represents their index in the AIG. I would use the "key" value, but the edge "index" can be identical
    #   for two different "edges" within the graph (the output of an AND feeds the input of two other ANDs etc)

    edges = {}  # Keep track of edges until file parse complete

    # 1. Parse header to get counts of all the different parts of the design.
    header_entries = lines[0].split()
    if len(header_entries) != 6:
        print(
            "ERROR. AIG header isn't correct length. Length ="
            f" {len(header_entries)},\n\tcontent = {header_entries}",
        )
        errors += 1
    file_type = header_entries[0]
    max_var_index = int(header_entries[1])
    input_count = int(header_entries[2])
    latch_count = int(header_entries[3])
    output_count = int(header_entries[4])
    AND_count = int(header_entries[5])

    # Info print statement
    print(
        f"This AIG is of type {file_type},\n\tmax index is"
        f" {max_var_index},\n\t{input_count} inputs,\n\t{latch_count} latches,\n\t{output_count} outputs,\n\tand"
        f" {AND_count} and gates.",
    )

    # 2. Find the header-indicated number of inputs and add them as nodes with type INPUT
    for i in range(
        1,
        (1 + input_count),
    ):  # Start after the header, end after header+input_count lines
        if debug:
            print(f"Inspecting line {i} as an INPUT: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) > 1:  # Should only have one index on an input line
            print(
                f"ERROR, expecting INPUT line but got more than one index: {lines[i]}",
            )
            errors += 1
            continue

        # Add the input to the graph as a new node.
        input_index = int(indices_on_line[0])
        aig_graph.add_node(input_index, type="INPUT")

    # 3. Find header-indicated number of latches and add them to list of nodes.
    for i in range(
        (1 + input_count),
        (1 + input_count + latch_count),
    ):  # Start with line after inputs, end after latches
        if debug:
            print(f"Inspecting line {i} as a LATCH: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) not in range(2, 4):  # Should have 2 or 3 values
            print(
                "ERROR, expecting LATCH line but there were"
                f" {len(indices_on_line)} indices on the line",
            )
            errors += 1
            continue

        # Add the latch as a node
        latch_index = int(indices_on_line[0])
        aig_graph.add_node(latch_index, type="LATCH")

    # 4. Find header-indicated number of outputs and add them to the graph as a node with type OUTPUT
    for i in range(
        (1 + input_count + latch_count),
        (1 + input_count + latch_count + output_count),
    ):  # Start after latch lines, end after output lines
        if debug:
            print(f"Inspecting line {i} as an OUTPUT: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) > 1:  # Should only have one index on an output line
            print(
                f"ERROR, expecting OUTPUT line but got more than one index: {lines[i]}",
            )
            errors += 1
            continue

        # Add it to the graph as a new node.
        output_index = int(indices_on_line[0])

        # Outputs are a bit tricky because they'll have the same index as the node that feeds them, and must be uniquely identified.
        # Let's try to just give it the index + "out" in string form.
        aig_graph.add_node(f"{output_index}_out", type="OUTPUT")

    # 5. Go through all AND lines in AIGER and add all of the result indices as nodes marked as AND
    for i in range(
        (1 + input_count + latch_count + output_count),
        (1 + input_count + latch_count + output_count + AND_count),
    ):  # Start after output lines, end after AND lines
        if debug:
            print(f"Inspecting line {i} as an AND: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) != 3:  # Should only 3 indices
            print(f"ERROR, expecting AND line but didn't have 3 indices: {lines[i]}")
            errors += 1
            continue

        # Add the result index to the graph as a new node.
        and_index = int(indices_on_line[0])
        aig_graph.add_node(and_index, type="AND")

    # 6. Revisit latches now that all nodes are added to the graph. Add edges to graph, accounting for inverse (odd-numbered) edges.
    for i in range(
        (1 + input_count),
        (1 + input_count + latch_count),
    ):  # Start with line after inputs, end after latches
        if debug:
            print(f"Inspecting line {i} as a LATCH to add edges: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) not in range(
            2,
            4,
        ):  # Should have 2 or 3 indices on the line
            print(
                "ERROR, expecting LATCH line but there were"
                f" {len(indices_on_line)} indices on the line",
            )
            errors += 1
            continue

        # Add the inputs to this latch as edges.
        node_index = int(indices_on_line[0])
        for line_location in range(1, len(indices_on_line)):
            index = int(indices_on_line[line_location])
            if index % 2:
                # It's an odd number, therefore, an inverse edge
                # Edge will go from the source node indicated by the current index to the sink node in the first position on this line
                # Source node will be the index given here minus one, since the source isn't odd/inversed.
                aig_graph.add_edge((index - 1), node_index, index=index, type="INVERSE")
            else:
                # Add edge the same way, but no need to adjust the index value and edge will be standard type.
                aig_graph.add_edge(index, node_index, index=index, type="STANDARD")

        # Now check to see if this node should feed an output, and create an edge if so.
        if aig_graph.has_node(f"{node_index}_out"):
            # Found non-inversed output. Add edge.
            aig_graph.add_edge(
                node_index,
                f"{node_index}_out",
                index=node_index,
                type="STANDARD",
            )
        elif aig_graph.has_node(f"{node_index + 1}_out"):
            # Found inversed output. Add edge.
            aig_graph.add_edge(
                node_index,
                f"{node_index + 1}_out",
                index=node_index,
                type="INVERSE",
            )

    # 7. Revisit ANDs identically to step #6 for latches.
    for i in range(
        (1 + input_count + latch_count + output_count),
        (1 + input_count + latch_count + output_count + AND_count),
    ):  # Start after output lines, end after AND lines
        if debug:
            print(f"Inspecting line {i} as an AND for adding edges: {lines[i]}")
        indices_on_line = lines[i].split()
        if len(indices_on_line) != 3:  # Should only 3 indices
            print(f"ERROR, expecting AND line but didn't have 3 indices: {lines[i]}")
            errors += 1
            continue

        # Add all the AND inputs as edges.
        node_index = int(indices_on_line[0])
        for line_location in range(1, len(indices_on_line)):
            index = int(indices_on_line[line_location])
            if index % 2:
                # It's an odd number, therefore, an inverse edge
                # Edge will go from the source node indicated by the current index to the sink node in the first position on this line
                # Source node will be the index given here minus one, since the source isn't odd/inversed.
                aig_graph.add_edge((index - 1), node_index, index=index, type="INVERSE")
            else:
                # Add edge the same way, but no need to adjust the index value and edge will be standard type.
                aig_graph.add_edge(index, node_index, index=index, type="STANDARD")

        # Now check to see if this node should feed an output, and create an edge if so.
        # print(f"Checking for node called {node_index}_out")
        if aig_graph.has_node(f"{node_index}_out"):
            # Found non-inversed output. Add edge.
            aig_graph.add_edge(
                node_index,
                f"{node_index}_out",
                index=node_index,
                type="STANDARD",
            )
        elif aig_graph.has_node(f"{node_index + 1}_out"):
            # Found inversed output. Add edge.
            aig_graph.add_edge(
                node_index,
                f"{node_index + 1}_out",
                index=node_index,
                type="INVERSE",
            )

    print(
        "Done traversing AIGER file and creating MultiDiGraph. Number of errors:"
        f" {errors}",
    )

    return aig_graph
