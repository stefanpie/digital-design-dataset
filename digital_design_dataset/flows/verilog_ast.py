import json
import random
import subprocess
import uuid
from pathlib import Path

import networkx as nx

# NEWLINE_CHARS = set(["\n", "\r", "\r\n"])

# RE_NODE_TYPE = re.compile(r"AST_(\w+)")
# RE_NODE_ID = re.compile(r"\[0x([0-9a-f]+)\]")
# RE_NODE_FILE_LOCATION = re.compile(r"<(.*?)>")


# def split_props_string(props_string: str) -> list[str]:
#     working_string = props_string
#     in_single_quotes = False
#     current_part = ""
#     parts = []
#     while len(working_string) > 0:
#         if working_string[0] == "'":
#             in_single_quotes = not in_single_quotes
#             current_part += working_string[0]
#             working_string = working_string[1:]
#         elif (
#             len(working_string) > 0
#             and working_string[0] == " "
#             and not in_single_quotes
#         ):
#             current_part = current_part.strip()
#             if current_part != "":
#                 parts.append(current_part)
#             current_part = ""
#             working_string = working_string[1:]
#         else:
#             current_part += working_string[0]
#             working_string = working_string[1:]
#     current_part = current_part.strip()
#     if current_part != "":
#         parts.append(current_part)
#     return parts


# def split_props_string(props_string: str) -> list[str]:
#     parts = []
#     current_part = ""
#     in_single_quotes = False
#     for i in range(len(props_string)):
#         char = props_string[i]
#         if char == "'":
#             in_single_quotes = not in_single_quotes
#             current_part += char
#         elif char == " " and not in_single_quotes:
#             current_part = current_part.strip()
#             if current_part != "":
#                 parts.append(current_part)
#             current_part = ""
#         else:
#             current_part += char
#     current_part = current_part.strip()
#     if current_part != "":
#         parts.append(current_part)
#     return parts


# def equal_sgin_not_in_quotes(single_prop_string: str) -> int | None:
#     in_single_quotes = False
#     for i, char in enumerate(single_prop_string):
#         if char == "'":
#             in_single_quotes = not in_single_quotes
#         elif char == "=" and not in_single_quotes:
#             return i
#     return None


# PROP_STR_PATTERN = re.compile(r"str='.*'(?: |$)")


# def props_string_to_dict(props_string: str) -> dict[str, str]:
#     # prop_parts = split_props_string(props_string)
#     # props_dict = {}
#     # for prop_part in prop_parts:
#     #     r = equal_sgin_not_in_quotes(prop_part)
#     #     if r is not None:
#     #         equal_sign_index = r
#     #         key = prop_part[:equal_sign_index].strip()
#     #         value = prop_part[equal_sign_index + 1 :].strip()
#     #         # value = value[1:-1]
#     #         props_dict[key] = value
#     #     else:
#     #         key, value = prop_part, prop_part
#     #         props_dict[key] = value
#     # return props_dict

#     # find all instances of str='.*'<space> or str='.*'<end of string>
#     # remove them and add them to the dict

#     # TODO: look into regex for pulling all the props out

#     props_string_working = props_string

#     porp_str = PROP_STR_PATTERN.findall(props_string_working)
#     props_dict = {}
#     for prop_str in porp_str:
#         key = "str"
#         value = prop_str[4:]
#         props_dict[key] = value

#     props_string_working = PROP_STR_PATTERN.sub("", props_string_working)

#     prop_parts = split_props_string(props_string_working)
#     for prop_part in prop_parts:
#         r = equal_sgin_not_in_quotes(prop_part)
#         if r is not None:
#             equal_sign_index = r
#             key = prop_part[:equal_sign_index].strip()
#             value = prop_part[equal_sign_index + 1 :].strip()
#             # value = value[1:-1]
#             props_dict[key] = value
#         else:
#             key, value = prop_part, prop_part
#             props_dict[key] = value
#     return props_dict


# def split_lines_not_in_quotes(raw_text: str) -> list[str]:
#     in_single_quotes = False
#     current_line = ""
#     lines = []
#     for char in raw_text:
#         if char == "'":
#             in_single_quotes = not in_single_quotes
#         elif char == "\n" and not in_single_quotes:
#             if current_line:
#                 lines.append(current_line)
#             current_line = ""
#         else:
#             current_line += char
#     if current_line:
#         lines.append(current_line)
#     return lines


# def raw_ast_to_tree(raw_ast: str) -> nx.DiGraph:
#     T = nx.MultiDiGraph()
#     T.add_node("root", type="AST_ROOT")

#     # lines = raw_ast.splitlines()
#     lines = split_lines_not_in_quotes(raw_ast)
#     lines = [line for line in lines if line.strip() != ""]

#     for line in lines:
#         node_type = line.lstrip().split(" ", maxsplit=1)[0]
#         if not (node_type.startswith("AST_") or node_type.startswith("ATTR")):
#             raise RuntimeError(f"Line does not start with 'AST_' or 'ATTR': {line}")

#     min_indent = min([len(line) - len(line.lstrip()) for line in lines])
#     indent_factor = 2

#     stack = ["root"]

#     node_ids = []

#     for line in lines:
#         line = line[min_indent:]
#         indent_level = (len(line) - len(line.lstrip())) // indent_factor

#         if line.strip().startswith("ATTR"):
#             node_id = stack[-1] + "_ATTR"
#             node_type = "ATTR"
#             value = line.strip().removeprefix("ATTR ")
#             node_data = {"type": node_type, "value": value}
#         else:
#             node_type_match = RE_NODE_TYPE.search(line)
#             if node_type_match is None:
#                 raise RuntimeError(f"Could not find node type in line: {line}")
#             node_type = node_type_match.group(0)

#             node_id_match = RE_NODE_ID.search(line)
#             if node_id_match is None:
#                 raise RuntimeError(f"Could not find node id in line: {line}")
#             node_id = node_id_match.group(1)

#             node_file_location_match = RE_NODE_FILE_LOCATION.search(line)
#             if node_file_location_match is None:
#                 raise RuntimeError(f"Could not find node file location in line: {line}")
#             node_file_location = node_file_location_match.group(1)

#             file_loaction_data = {}
#             file_loaction_data["path"] = node_file_location.split(":")[0]
#             file_loaction_data["line_start"] = int(
#                 node_file_location.split(":")[1].split("-")[0].split(".")[0]
#             )
#             file_loaction_data["col_start"] = int(
#                 node_file_location.split(":")[1].split("-")[0].split(".")[1]
#             )
#             file_loaction_data["line_end"] = int(
#                 node_file_location.split(":")[1].split("-")[1].split(".")[0]
#             )
#             file_loaction_data["col_end"] = int(
#                 node_file_location.split(":")[1].split("-")[1].split(".")[1]
#             )

#             # props = {}
#             # for prop in line.split()[3:]:
#             #     if "=" in prop:
#             #         key, value = prop.split("=", maxsplit=1)
#             #         props[key] = value
#             #     else:
#             #         key, value = prop, prop
#             #         props[key] = value

#             if len(line.split(maxsplit=3)) < 4:
#                 props = {}
#             else:
#                 props_string = line.split(maxsplit=3)[3]
#                 props = props_string_to_dict(props_string)

#             node_data = {
#                 "type": node_type,
#                 "file_location": file_loaction_data,
#                 "node_props": props,
#             }

#         T.add_node(node_id, **node_data)
#         T.add_edge(stack[indent_level], node_id, t_edge_type="ast")
#         node_ids.append(node_id)
#         stack = stack[: indent_level + 1]
#         stack.append(node_id)

#     # add egdes between nodes in natural code order
#     for i in range(len(node_ids)):
#         if i < len(node_ids) - 1:
#             T.add_edge(node_ids[i], node_ids[i + 1], t_edge_type="nco")

#     # add reverse edges for ast edges and nco edges
#     for u, v, d in T.edges(data=True):
#         if d["t_edge_type"] == "ast":
#             T.add_edge(v, u, t_edge_type="ast_reverse")
#         elif d["t_edge_type"] == "nco":
#             T.add_edge(v, u, t_edge_type="nco_reverse")

#     # find the module node
#     module_nodes = list(filter(lambda x: T.nodes[x]["type"] == "AST_MODULE", T.nodes))
#     if len(module_nodes) == 0:
#         raise RuntimeError("Could not find AST_MODULE node")
#     elif len(module_nodes) > 1:
#         raise RuntimeError("Found more than one AST_MODULE node")
#     module_node = module_nodes[0]
#     module_name = T.nodes[module_node]["node_props"]["str"]
#     if module_name[0] == "'" and module_name[-1] == "'":
#         module_name = module_name[1:-1]

#     all_nodes_not_root = list(filter(lambda x: x != "root", T.nodes))
#     # reanme all the nodes to include the module name
#     mapping = {node: f"{module_name}_{node}" for node in all_nodes_not_root}
#     T = nx.relabel_nodes(T, mapping)

#     return T


# def empty_ast() -> nx.DiGraph:
#     T = nx.MultiDiGraph()
#     T.add_node("root", type="AST_ROOT")
#     return T


# def verilog_ast(verilog_file: Path, yoysys_bin: str = "yosys"):
#     """Returns the AST of a verilog file"""

#     print(verilog_file)

#     ast_temp_file = tempfile.NamedTemporaryFile(suffix=".ast")

#     script = ""
#     script += f"tee -o {ast_temp_file.name} read_verilog -dump_ast1 {verilog_file};"
#     ys_temp_file = tempfile.NamedTemporaryFile(suffix=".ys")
#     ys_temp_file.write(script.encode())
#     ys_temp_file.read()

#     p = subprocess.run(
#         [yoysys_bin, "-q", "-s", str(ys_temp_file.name)], capture_output=True
#     )
#     if p.returncode != 0:
#         print(p.stdout.decode())
#         print(p.stderr.decode())
#         raise RuntimeError("Yosys failed with return code: " + str(p.returncode))

#     ys_temp_file.close()

#     ast_raw = ast_temp_file.read().decode().strip()
#     ast_temp_file.close()

#     ast_graphs = []

#     ast_dump_search = re.findall(
#         "Dumping AST before simplification:(.*?)--- END OF AST DUMP ---",
#         ast_raw,
#         re.DOTALL,
#     )

#     if len(ast_dump_search) == 0:
#         if "Successfully finished Verilog frontend." in ast_raw:
#             ast_graphs.append(empty_ast())
#         else:
#             raise RuntimeError("Could not find AST in Yosys output")

#     for ast_match in ast_dump_search:
#         ast_graphs.append(raw_ast_to_tree(ast_match))

#     if len(ast_graphs) > 1:
#         ast_tree_graph = nx.compose_all(ast_graphs)
#     else:
#         ast_tree_graph = ast_graphs[0]

#     return ast_tree_graph


# def add_nodes_and_edges(G, node, parent=None):
#     if node is None:
#         return
#     node_id = node.get("tag", None)
#     G.add_node(node_id, **node)  # Add node with attributes
#     if parent:
#         G.add_edge(parent, node_id)  # Add edge from parent to this node

#     for child in node.get("children", []):
#         add_nodes_and_edges(G, child, parent=node_id)


def generate_node_id(node, rd):
    # start = node.get("start")
    # end = node.get("end")
    # tag = node.get("tag")
    # return f"{tag}_{start}_{end}"

    node_id = str(uuid.UUID(int=rd.getrandbits(128)))
    return node_id


def add_nodes_and_edges(G, node, rd, parent=None):
    if node is None:
        return

    node_id = generate_node_id(node, rd)
    node_data_keys = list(node.keys())
    node_data_keys = [k for k in node_data_keys if k != "children"]
    node_data = {k: node[k] for k in node_data_keys}
    G.add_node(node_id, **node_data)  # Add node with attributes
    if parent:
        G.add_edge(parent, node_id, t_edge_type="ast")

    for child in node.get("children", []):
        add_nodes_and_edges(G, child, rd, parent=node_id)


def verilog_ast(
    verilog_file: Path,
    verible_verilog_syntax_bin: str = "verible-verilog-syntax",
) -> nx.DiGraph | None:
    print(verilog_file)

    p = subprocess.run(
        [
            verible_verilog_syntax_bin,
            "--export_json",
            "--printtree",
            str(verilog_file.resolve()),
        ],
        capture_output=True,
        check=False,
    )

    if p.returncode != 0:
        ast_json = json.loads(p.stdout.decode())
        try:
            ast_json = json.loads(p.stdout.decode())
            if "errors" in list(ast_json.values())[0]:
                print(p.stdout.decode())
                print("Verible returned an error")
                return None
        except:  # noqa: E722
            print(p.stdout.decode())
            print(p.stderr.decode())
            raise RuntimeError("Verible failed with return code: " + str(p.returncode))

    ast_json = json.loads(p.stdout.decode())

    if len(ast_json) > 1 or len(ast_json) == 0:
        print("Verible returned more than one AST")

    tree_data = list(ast_json.values())[0]["tree"]

    rd = random.Random()
    rd.seed(0)

    G = nx.DiGraph()
    add_nodes_and_edges(G, tree_data, rd)

    # check if G is a tree
    if not nx.is_tree(G):
        raise RuntimeError("AST is not a tree")

    # add reverse ast edges
    for u, v, d in G.edges(data=True):
        if d["t_edge_type"] == "ast":
            G.add_edge(v, u, t_edge_type="ast_reverse")

    # add forward and reverse nco edges
    all_nodes = list(G.nodes)
    for i in range(len(all_nodes)):
        if i < len(all_nodes) - 1:
            G.add_edge(all_nodes[i], all_nodes[i + 1], t_edge_type="nco")
        if i > 0:
            G.add_edge(all_nodes[i], all_nodes[i - 1], t_edge_type="nco_reverse")

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

    return G
