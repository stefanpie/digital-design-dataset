import json
import operator
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from pprint import pp

import networkx as nx

from digital_design_dataset.design_dataset import HARDWARE_DATA_TEXT_EXTENSIONS_SET


def run_yosys_for_data(source_files: list[Path]) -> dict:
    json_data_file = tempfile.NamedTemporaryFile(suffix=".json")

    script = ""
    for source_file in source_files:
        script += f"read_verilog {source_file};\n"
    script += "hierarchy;\n"
    script += "proc;\n"
    script += f"write_json {json_data_file.name};\n"

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        raise FileNotFoundError("yosys executable not found in PATH")

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"yosys failed with return code {p.returncode}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}",
        )

    data_yosys = json.load(json_data_file)

    return data_yosys


RE_YOSYS_SRC_ATTR = re.compile(r"\(\* src =.*?\*\)")


def run_yosys_for_sub_design(
    source_files: list[Path],
    top_module: str,
    modules_to_remove: set[str],
) -> str:
    output_verilog_file = tempfile.NamedTemporaryFile(suffix=".v")
    rename_list_file = tempfile.NamedTemporaryFile(suffix=".txt")

    script = ""
    for source_file in source_files:
        script += f"read_verilog -noblackbox {source_file};\n"
    # script += f"hierarchy -check -top {top_module};\n"
    for module_name in modules_to_remove:
        script += f"delete {module_name};\n"
    script += "proc;\n"
    script += "opt_clean;\n"
    script += "opt;\n"
    script += "opt_clean;\n"
    script += f"select -list -write {rename_list_file.name} t:*$func$*;\n"
    script += f"write_verilog -noparallelcase -noattr {output_verilog_file.name};\n"

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        raise FileNotFoundError("yosys executable not found in PATH")

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"yosys failed with return code {p.returncode}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}",
        )

    source = Path(output_verilog_file.name).read_text()
    source = "\n".join(source.splitlines()[2:])
    # print(source)

    rename_list = Path(rename_list_file.name).read_text()
    rename_list = [line.strip() for line in rename_list.splitlines() if line.strip()]

    identifiers = []
    for line in rename_list:
        identifier = line.split(" ")[0]
    # pp(identifiers)

    # TODO: handel personal / system / path identifiers being leaked by yosys
    # yosys names internal elaborated stuff sometimes using absolute paths
    # this leaks personal information about the system and user who runs the
    # this code which is used in the structured decomposition approach

    return source


# def extract_design_dag(data_yosys: dict) -> nx.DiGraph:
#     g = nx.DiGraph()

#     module_names = set(data_yosys["modules"].keys())
#     # print(module_names)
#     for module_name in module_names:
#         g.add_node(module_name, module_name=module_name)

#     for module_name, module_data in data_yosys["modules"].items():
#         cells = module_data.get("cells", {})
#         for _cell_name, cell_data in cells.items():
#             if cell_data["type"] in module_names:
#                 g.add_edge(module_name, cell_data["type"])

#     if not nx.is_directed_acyclic_graph(g):
#         raise RuntimeError("Design hierarchy is not a DAG")
#     return g


def extract_design_dag(data_yosys: dict) -> nx.DiGraph:
    # pp(data_yosys)
    # /tmp/tmpmqq_4c0c.json
    # json_data_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    # Path(json_data_file.name).write_text(json.dumps(data_yosys, indent=4))
    # pp(json_data_file.name)

    if len(data_yosys["modules"]) == 0:
        raise ValueError("No modules found in Yosys data")
    # module_names = list(set(data_yosys["modules"].keys()))

    module_regular_names = []
    module_para_names = []
    module_para_to_reg_map: dict[str, str] = {}

    for name in data_yosys["modules"]:
        if "hdlname" not in data_yosys["modules"][name]["attributes"]:
            module_regular_names.append(name)
        if "hdlname" in data_yosys["modules"][name]["attributes"]:
            module_para_names.append(name)
            module_para_to_reg_map[name] = data_yosys["modules"][name]["attributes"]["hdlname"]

    final_module_names = set(module_regular_names) | {module_para_to_reg_map[n] for n in module_para_names}

    final_module_data = {n: {} for n in final_module_names}

    for module_name in final_module_names:
        final_module_data[module_name]["submodules"] = set()

    for module_name in data_yosys["modules"].keys():
        module_cells = data_yosys["modules"][module_name]["cells"]
        module_cells = {k: v for k, v in module_cells.items() if v["type"] in data_yosys["modules"]}
        module_cells_type = [v["type"] for v in module_cells.values()]
        module_cell_types = set(module_cells_type)
        module_cell_types_mapped = {module_para_to_reg_map.get(t, t) for t in module_cell_types}

        if module_name in final_module_names:
            entry_name = module_name
        else:
            entry_name = module_para_to_reg_map[module_name]

        final_module_data[entry_name]["submodules"] |= module_cell_types_mapped
        final_module_data[entry_name]["module_name"] = entry_name

    g = nx.DiGraph()
    nodes_added = set()
    for module_data in final_module_data.values():
        g.add_node(module_data["module_name"], module_name=module_data["module_name"])
        nodes_added.add(module_data["module_name"])

    for module_data in final_module_data.values():
        for submodule in module_data["submodules"]:
            g.add_edge(module_data["module_name"], submodule)

    if not nx.is_directed_acyclic_graph(g):
        raise RuntimeError("Design hierarchy is not a DAG")

    return g


def extract_unique_subgraphs(
    g: nx.DiGraph,
    all_module_list: list[str],
) -> list[nx.DiGraph]:
    sub_designs = []
    for module_name in all_module_list:
        subgraph: nx.DiGraph = g.subgraph(
            nx.descendants(g, module_name) | {module_name},
        ).copy()
        isomorphic = False
        # print(f"Checking subgraph: {subgraph.nodes}")
        for sub_design in sub_designs:
            if nx.is_isomorphic(
                subgraph,
                sub_design,
                node_match=lambda x, y: x["module_name"] == y["module_name"],
            ):
                # print(f"Isomorphic with {sub_design.nodes}")
                isomorphic = True
                break
        if not isomorphic:
            sub_designs.append(subgraph)
    return sub_designs


def find_top_node(sub_design: nx.DiGraph) -> str:
    nodes_with_no_in_edges = [node for node in sub_design.nodes if sub_design.in_degree(node) == 0]
    if len(nodes_with_no_in_edges) != 1:
        raise ValueError(
            "Sub-design does not have a unique root node",
        )
    root_node = nodes_with_no_in_edges[0]
    return root_node


def simple_synth_check_yosys(
    sources: dict[str, str],
    top_module: str,
    extra_data_files: list[Path] | None = None,
) -> bool:
    temp_inputs = []
    # temp_dir = tempfile.TemporaryDirectory()
    # temp_dir_name = temp_dir.name
    temp_dir = tempfile.mkdtemp()
    temp_dir_name = temp_dir

    for source_name, source in sources.items():
        temp_input = Path(temp_dir_name) / source_name
        temp_inputs.append(temp_input)
        temp_input.write_text(source)
        print(temp_input)

    # add extra data files
    if extra_data_files is not None:
        for extra_data_file in extra_data_files:
            if extra_data_file.suffix not in HARDWARE_DATA_TEXT_EXTENSIONS_SET:
                raise ValueError(
                    f"Extra data file {extra_data_file} is not a hardware data file",
                )
            temp_extra_data_file = Path(temp_dir_name) / extra_data_file.name
            shutil.copy(extra_data_file, temp_extra_data_file)

    script = ""
    for temp_input in temp_inputs:
        script += f"read_verilog {temp_input.name};\n"
    script += f"hierarchy -check -top {top_module};\n"
    script += "prep;\n"

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        raise FileNotFoundError("yosys executable not found in PATH")

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script],
        check=False,
        capture_output=True,
        text=True,
        cwd=temp_dir_name,
    )

    if p.returncode != 0:
        print(
            f"yosys failed with return code {p.returncode}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}",
        )
        return False

    return True


def compute_hierarchy_structured(source_files: list[Path]) -> nx.DiGraph:
    data_yosys = run_yosys_for_data(source_files)
    g = extract_design_dag(data_yosys)

    return g


def decompose_design_structured(source_files: list[Path]) -> dict[str, dict[str, str]]:
    # Decompose a verilog design into multiple sub designs based on module hierarchy.
    # using Yosys to read the design, using networkx to extract unique subgraphs,
    # and using Yosys again to generate the Verilog source for each sub-design
    # corresponding to each unique subgraph.

    # Each sub-design is a distinct subgraph of the design hierarchy graph,
    # where each defined module corresponds to a sub-design with that module
    # as the top module along with all its dependent modules.

    # The result is a list of single-file Verilog designs for each unique sub-design,
    # with all the necessary modules defined for that sub-design.

    # Note that the generated sub-designs' Verilog source is auto-generated from Yosys.
    # The `read_verilog`, `hierarchy`, `proc`, `rename`, and `write_verilog` commands
    # are used, making subtle changes to the design (semantically and syntactically)
    # that may not match the original source files.

    # For this reason, we recommend using this decomposition for generating
    # data for tasks *not* related to the source code structure and syntax.
    # In other words, this decomposition is useful for extracting sub-designs for
    # downstream EDA tasks focused on the actual generated hardware
    # and netlists, such as synthesis and implementation.
    # The syntactic and source code changes for these EDA applications are not
    # as relevant and the design semantic changes that Yosys makes are minimal.

    # Also, since this decomposition is more structured, programmatic, and extracted
    # using Yosys, the generated sub-designs should be synthesizable as
    # long as the original design source is synthesizable (barring any Yosys
    # quirks or unseen edge cases).

    # For applications that require the original source code structure, syntax,
    # and identifiers, such as for use with large language models,
    # this style of decomposition is not recommended.

    data_yosys = run_yosys_for_data(source_files)

    g = extract_design_dag(data_yosys)

    all_module_list = list(nx.lexicographical_topological_sort(g))

    sub_designs = extract_unique_subgraphs(g, all_module_list)

    sub_design_data = {}
    for sub_design in sub_designs:
        top_node = find_top_node(sub_design)
        decendents = nx.descendants(g, top_node) | {top_node}
        modules_to_remove = set(all_module_list) - decendents

        source = run_yosys_for_sub_design(source_files, top_node, modules_to_remove)
        sub_design_data[top_node] = {}
        sub_design_data[top_node][f"{top_node}.v"] = source

    novel_design_count = len(sub_design_data) - len(all_module_list)
    if novel_design_count > 0:
        print(f"NOVEL SUB-DESIGNS: {novel_design_count}")

    # check synthesizability
    for top_node, source in sub_design_data.items():
        if not simple_synth_check_yosys(source, top_node):
            raise RuntimeError("Sub-design is not synthesizable")

    return sub_design_data


RE_MODULE = re.compile(r"module(.|\s)*?endmodule", re.MULTILINE)


def yosys_read_module(module_str: str) -> dict:
    # read the module string into a Yosys and dump the JSON data

    input_file = tempfile.NamedTemporaryFile(suffix=".v")
    output_file = tempfile.NamedTemporaryFile(suffix=".json")

    Path(input_file.name).write_text(module_str)

    script = f"read_verilog {input_file.name};\n"
    script += "proc;\n"
    script += f"write_json {output_file.name};\n"

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        raise FileNotFoundError("yosys executable not found in PATH")

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"yosys failed with return code {p.returncode}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}",
        )

    data_yosys = json.load(output_file)

    return data_yosys


def compute_hierarchy_text(source_files: list[Path]) -> nx.DiGraph:
    data_yosys = run_yosys_for_data(source_files)

    if len(data_yosys["modules"]) == 0:
        raise ValueError("No modules found in Yosys data")

    module_regular_names = []
    module_para_names = []
    module_para_to_reg_map: dict[str, str] = {}

    for name in data_yosys["modules"]:
        if "hdlname" not in data_yosys["modules"][name]["attributes"]:
            module_regular_names.append(name)
        if "hdlname" in data_yosys["modules"][name]["attributes"]:
            module_para_names.append(name)
            module_para_to_reg_map[name] = data_yosys["modules"][name]["attributes"]["hdlname"]

    final_module_names = set(module_regular_names) | {module_para_to_reg_map[n] for n in module_para_names}

    final_module_data = {n: {} for n in final_module_names}

    for module_name in final_module_names:
        found_count = 0
        for source_file in source_files:
            source = source_file.read_text()
            re_str = r"module\s+?" + module_name + r"(?:\s|\(|#|;)(.|\s)*?endmodule"
            module_match = re.search(re_str, source, re.MULTILINE)
            if module_match is not None:
                # check to make sure line with keyword matched to "module" is not
                # a single line comment right before an instance of the module
                # would look like this:
                # ---
                # // blah blah blah module
                # my_module my_module_inst (...
                # ---
                # we want to skip this match
                start_line_number = source.count("\n", 0, module_match.start()) + 1
                start_line = source.splitlines()[start_line_number - 1]
                start_line_strip = start_line.strip()
                if start_line_strip.startswith("//"):
                    continue

                # also handle case where the comment does not start
                # at the beginning of the line
                if "//" in start_line_strip:  # simple check before expensive regex check
                    comment_match = re.search(
                        r"((\/[*])([\s\S]+)([*]\/))|([/]{2,}[^\n]+)",
                        start_line,
                    )
                    # assert comment_match is not None
                    if comment_match is None:
                        raise ValueError(
                            "Comment regex match failed even if // in line",
                        )
                    # find the location of the start of the match
                    comment_start = start_line.find(comment_match.group())
                    # if the comment starts before the module keyword, skip this match
                    if comment_start < start_line.find("module"):
                        continue

                final_module_data[module_name]["source"] = module_match.group()
                final_module_data[module_name]["source_file"] = source_file
                found_count += 1
        if found_count != 1:
            raise ValueError(
                f"Module {module_name} not found in exactly one source file",
            )

    for module_name in final_module_names:
        final_module_data[module_name]["submodules"] = set()

    for module_name in data_yosys["modules"].keys():
        module_cells = data_yosys["modules"][module_name]["cells"]
        module_cells = {k: v for k, v in module_cells.items() if v["type"] in data_yosys["modules"]}
        module_cells_type = [v["type"] for v in module_cells.values()]
        module_cell_types = set(module_cells_type)
        module_cell_types_mapped = {module_para_to_reg_map.get(t, t) for t in module_cell_types}

        if module_name in final_module_names:
            entry_name = module_name
        else:
            entry_name = module_para_to_reg_map[module_name]

        final_module_data[entry_name]["submodules"] |= module_cell_types_mapped

        final_module_data[entry_name]["module_name"] = entry_name

    g = nx.DiGraph()
    nodes_added = set()
    for module_data in final_module_data.values():
        g.add_node(module_data["module_name"], module_name=module_data["module_name"])
        nodes_added.add(module_data["module_name"])

    for module_data in final_module_data.values():
        for submodule in module_data["submodules"]:
            g.add_edge(module_data["module_name"], submodule)

    if not nx.is_directed_acyclic_graph(g):
        raise RuntimeError("Design hierarchy is not a DAG")

    return g


def decompose_design_text(
    source_files: list[Path],
    extra_data_files: list[Path] | None = None,
) -> dict[str, dict[str, str]]:
    # This decomposition is a simpler version of `decompose_design_structured`.
    # The extraction is done using heuristic text manipulation and processing.

    # Even though text manipulation is ad-hoc and not as robust as
    # structured decomposition, it can preserve the original source
    # code structure, syntax, and identifiers.

    # This decomposition is useful for applications requiring the original
    # source code structure, syntax, and identifiers,
    # such as use with large language models.

    # As mentioned, this approach is not as robust as structured
    # decomposition and must handle many edge cases.
    # For example, this approach can robustly identify module definitions,
    # module instantiations, and module bodies.
    # Additionally, Verilog macros such as ifdefs around module definitions and
    # instantiations cannot be handled since they include arbitrary source code
    # transformation logic we cannot copy into decomposed designs.

    # We make some effort to handle include statements, define statements,
    # timescale statements, and standalone parameter statements (all of which
    # can be defined outside module bodies).
    # These are common in real-world designs and can be handled more
    # easily than arbitrary macros.

    # We also make some effort in this approach to maintain the original file structure
    # of the original source code instead of emitting each sub-design as a single file
    # with all sources concatenated together.
    # For example, if the original source code has multiple modules defined in
    # different Verilog files, we can preserve and emit the files separately as
    # organized in the original sources with the selected modules part of a sub-design.
    # This is also advantageous to preserving file structure for source code
    # analysis and more complex applications of large language models.

    # This is done by removing the source text for all
    # modules bodies except the modules you want to keep.
    # This also has the advantage that you get to keep the rest of the source text
    # outside module bodies intact, include edge cases such as include statements,
    # define statements, timescale statements, and standalone parameter statements.
    # The main disadvantage of this approach is that you have to deal with awkward
    # leftover whitespace. This is not major when dealing with extra lines inside files.
    # The only annoying edge case is when a file with only a single module
    # is not part of the sub-designs. This leave an empty file that needs to be removed.

    # This approach implies that not all generated sub-designs may be synthesizable with
    # this decomposition, even if the original design is synthesizable.
    # We add a simple flag that also runs a quick synthesizability check on
    # generated sub-designs using Yosys.

    data_yosys = run_yosys_for_data(source_files)

    if len(data_yosys["modules"]) == 0:
        raise ValueError("No modules found in Yosys data")

    module_regular_names = []
    module_para_names = []
    module_para_to_reg_map: dict[str, str] = {}

    for name in data_yosys["modules"]:
        if "hdlname" not in data_yosys["modules"][name]["attributes"]:
            module_regular_names.append(name)
        if "hdlname" in data_yosys["modules"][name]["attributes"]:
            module_para_names.append(name)
            module_para_to_reg_map[name] = data_yosys["modules"][name]["attributes"]["hdlname"]

    final_module_names = set(module_regular_names) | {module_para_to_reg_map[n] for n in module_para_names}

    final_module_data = {n: {} for n in final_module_names}

    for module_name in final_module_names:
        found_count = 0
        for source_file in source_files:
            source = source_file.read_text()
            re_str = r"module\s+?" + module_name + r"(?:\s|\(|#)(.|\s)*?endmodule"
            module_match = re.search(re_str, source, re.MULTILINE)
            if module_match is not None:
                # check to make sure line with keyword matched to "module" is not
                # a single line comment right before an instance of the module
                # would look like this:
                # ---
                # // blah blah blah module
                # my_module my_module_inst (...
                # ---
                # we want to skip this match
                start_line_number = source.count("\n", 0, module_match.start()) + 1
                start_line = source.splitlines()[start_line_number - 1]
                start_line_strip = start_line.strip()
                if start_line_strip.startswith("//"):
                    continue

                # also handle case where the comment does not start
                # at the beginning of the line
                if "//" in start_line_strip:  # simple check before expensive regex check
                    comment_match = re.search(
                        r"((\/[*])([\s\S]+)([*]\/))|([/]{2,}[^\n]+)",
                        start_line,
                    )
                    # assert comment_match is not None
                    if comment_match is None:
                        raise ValueError(
                            "Comment regex match failed even if // in line",
                        )
                    # find the location of the start of the match
                    comment_start = start_line.find(comment_match.group())
                    # if the comment starts before the module keyword, skip this match
                    if comment_start < start_line.find("module"):
                        continue

                final_module_data[module_name]["source"] = module_match.group()
                final_module_data[module_name]["source_file"] = source_file
                found_count += 1
        if found_count != 1:
            raise ValueError(
                f"Module {module_name} not found in exactly one source file",
            )

    for module_name in final_module_names:
        final_module_data[module_name]["submodules"] = set()

    for module_name in data_yosys["modules"].keys():
        module_cells = data_yosys["modules"][module_name]["cells"]
        module_cells = {k: v for k, v in module_cells.items() if v["type"] in data_yosys["modules"]}
        module_cells_type = [v["type"] for v in module_cells.values()]
        module_cell_types = set(module_cells_type)
        module_cell_types_mapped = {module_para_to_reg_map.get(t, t) for t in module_cell_types}

        if module_name in final_module_names:
            entry_name = module_name
        else:
            entry_name = module_para_to_reg_map[module_name]

        final_module_data[entry_name]["submodules"] |= module_cell_types_mapped

        final_module_data[entry_name]["module_name"] = entry_name

    g = nx.DiGraph()
    nodes_added = set()
    for module_data in final_module_data.values():
        g.add_node(module_data["module_name"], module_name=module_data["module_name"])
        nodes_added.add(module_data["module_name"])

    for module_data in final_module_data.values():
        for submodule in module_data["submodules"]:
            g.add_edge(module_data["module_name"], submodule)

    if not nx.is_directed_acyclic_graph(g):
        raise RuntimeError("Design hierarchy is not a DAG")

    all_module_list = list(nx.lexicographical_topological_sort(g))
    sub_designs = extract_unique_subgraphs(g, all_module_list)

    sub_design_sources = {}
    for sub_design in sub_designs:
        top_node = find_top_node(sub_design)
        sub_design_sources[top_node] = {}
        # for each original source file, load into the sub-design
        for fp in source_files:
            sub_design_sources[top_node][fp.name] = fp.read_text()

        nodes_in_sub_design = sub_design.nodes
        nodes_not_in_sub_design = set(all_module_list) - nodes_in_sub_design

        module_bodies_not_in_sub_design = []
        for module_data in final_module_data.values():
            if module_data["module_name"] in nodes_not_in_sub_design:
                module_bodies_not_in_sub_design.append(module_data["source"])

        for module_body in module_bodies_not_in_sub_design:
            for source_fp_name in sub_design_sources[top_node]:
                txt = sub_design_sources[top_node][source_fp_name]
                txt = txt.replace(module_body, "\n")
                sub_design_sources[top_node][source_fp_name] = txt

        for source_fp_name in sub_design_sources[top_node]:
            txt = sub_design_sources[top_node][source_fp_name]
            if txt.strip() == "":
                txt = txt.strip()
                continue
            txt = txt.rstrip("\n") + "\n"
            txt = txt.lstrip("\n")
            sub_design_sources[top_node][source_fp_name] = txt

        for source_fp_name in list(sub_design_sources[top_node]):
            txt = sub_design_sources[top_node][source_fp_name]
            if txt.strip() == "":
                del sub_design_sources[top_node][source_fp_name]

    # synthesizability check
    for top_node, sources in sub_design_sources.items():
        if not simple_synth_check_yosys(sources, top_node, extra_data_files):
            raise RuntimeError("Sub-design is not synthesizable")

    return sub_design_sources


def compute_hierarchy_redundent(source_files: list[Path]) -> nx.DiGraph:
    g_structured = compute_hierarchy_structured(source_files)
    g_text = compute_hierarchy_text(source_files)
    if not nx.is_isomorphic(g_structured, g_text, node_match=operator.eq):
        raise RuntimeError("Structured and text hierarchies are not isomorphic or don't have the same node properties")
    return g_structured


def get_top_nodes(g: nx.DiGraph) -> list[str]:
    top_nodes = [node for node in g.nodes if g.in_degree(node) == 0]
    return sorted(top_nodes)


def compute_top_modules(source_files: list[Path]) -> list[str]:
    g = compute_hierarchy_redundent(source_files)
    return get_top_nodes(g)
