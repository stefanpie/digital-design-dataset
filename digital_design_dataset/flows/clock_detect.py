import json
import re
import shutil
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, ClassVar

from joblib import Parallel, delayed

from digital_design_dataset.design_dataset import HARDWARE_DATA_TEXT_EXTENSIONS_SET
from digital_design_dataset.flows.decompose import auto_top
from digital_design_dataset.flows.flows import Flow


def run_yosys_for_rtlil(
    source_files: list[Path],
    top_module: str,
    cwd: Path | None = None,
) -> tuple[str, str, str, str]:
    rtill_file = NamedTemporaryFile()
    portlist_file = NamedTemporaryFile()
    rtlil_file_post_proc = NamedTemporaryFile()
    log_file = NamedTemporaryFile()

    script = ""
    for source_file in source_files:
        if source_file.suffix in HARDWARE_DATA_TEXT_EXTENSIONS_SET:
            continue
        script += f"read_verilog {source_file};\n"
    script += f"hierarchy -top {top_module};\n"
    script += "flatten;\n"
    script += f"write_rtlil {rtill_file.name};\n"
    script += "proc; opt;\n"
    script += f"write_rtlil {rtlil_file_post_proc.name};\n"
    script += f"tee -o {portlist_file.name} portlist;\n"

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        raise FileNotFoundError("yosys executable not found in PATH")

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script, "-l", log_file.name],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"yosys failed with return code {p.returncode}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}",
        )

    data_rtlil = rtill_file.read().decode("utf-8").strip()
    data_rtlil_post_proc = rtlil_file_post_proc.read().decode("utf-8").strip()
    portlist = portlist_file.read().decode("utf-8").strip()
    yosys_log = log_file.read().decode("utf-8").strip()
    return data_rtlil, data_rtlil_post_proc, portlist, yosys_log


def parse_syncs(rtlil_content: str) -> dict:
    sync_signals = {}
    process_blocks = re.findall(r"process (.*?)\n(.*?)\nend", rtlil_content, re.DOTALL)

    for process_name, process_body in process_blocks:
        # Find all 'sync posedge' and 'sync negedge' constructs
        sync_edges = re.findall(r"sync (posedge|negedge) (\\\S+)", process_body)
        for edge, sync_signal in sync_edges:
            if sync_signal not in sync_signals:
                sync_signals[sync_signal] = []
            sync_signals[sync_signal].append({
                "process": process_name.strip(),
                "edge": edge,
            })

    return sync_signals


def parse_port_list(port_list: str) -> list[dict[str, str | int]]:
    ports = []
    lines = port_list.strip().splitlines()

    for line in lines:
        match = re.match(r"(input|output)\s+\[(\d+):(\d+)\]\s+(\w+)", line.strip())
        if match:
            direction, msb, lsb, name = match.groups()
            is_single_bit = int(msb) == int(lsb)
            ports.append({
                "direction": direction,
                "name": name,
                "width": f"[{msb}:{lsb}]",
                "msb": int(msb),
                "lsb": int(lsb),
                "is_single_bit": is_single_bit,
            })

    return ports


def parse_connections(rtlil_content: str) -> dict[str, list[str]]:
    connections = defaultdict(list)
    connection_statements = re.findall(r"connect\s+\\(\S+)\s+\\(\S+)", rtlil_content)

    for target, source in connection_statements:
        connections[source].append(target)
    return connections


def trace_signal(graph: dict[str, list[str]], start_signal: str) -> set[str]:
    visited = set()
    queue = deque([start_signal])

    while queue:
        signal = queue.popleft()
        if signal not in visited:
            visited.add(signal)
            queue.extend(graph[signal])

    return visited


def filter_clock_candidate_semanitcly(candidate: str) -> bool:
    if candidate.lower().startswith(("rst_", "reset_")):
        return False
    if candidate.lower().endswith(("_rst", "_reset")):
        return False
    if candidate.lower() in {"rst", "reset"}:
        return False
    for keyword in ("_rst_", "_reset_"):
        if keyword in candidate.lower():
            return False

    if candidate.lower().startswith(("en_", "enable_")):
        return False
    if candidate.lower().endswith(("_en", "_enable")):
        return False
    if candidate.lower() in {"en", "enable"}:
        return False
    for keyword in ("_en_", "_enable_"):
        if keyword in candidate.lower():
            return False

    # do the same with "ready", "valid"
    if candidate.lower().startswith(("rdy_", "ready_")):
        return False
    if candidate.lower().endswith(("_rdy", "_ready")):
        return False
    if candidate.lower() in {"rdy", "ready"}:
        return False
    for keyword in ("_rdy_", "_ready_"):
        if keyword in candidate.lower():
            return False

    if candidate.lower().startswith(("vld_", "valid_")):
        return False
    if candidate.lower().endswith(("_vld", "_valid")):
        return False
    if candidate.lower() in {"vld", "valid"}:
        return False
    for keyword in ("_vld_", "_valid_"):
        if keyword in candidate.lower():
            return False

    return True


def detect_clocks(source_files: list[Path], top_module: str | None = None, cwd: Path | None = None) -> dict[str, Any]:
    if top_module is None:
        top = auto_top(source_files)
    else:
        top = top_module

    data_rtlil, data_rtlil_post_proc, portlist, yosys_log = run_yosys_for_rtlil(source_files, top, cwd=cwd)
    sync_data = parse_syncs(data_rtlil)
    port_data = parse_port_list(portlist)
    connection_data = parse_connections(data_rtlil)

    sync_names = list(sync_data.keys())
    sync_names_without_slash = [name.removeprefix("\\") for name in sync_names]
    port_names_single_bit_input = [
        port["name"] for port in port_data if port["is_single_bit"] and port["direction"] == "input"
    ]
    sync_names_set = set(sync_names_without_slash)
    port_names_set = set(port_names_single_bit_input)

    ports_traced: dict[str, list[str]] = {}
    for port in port_names_set:
        assert isinstance(port, str)
        port_trace = trace_signal(connection_data, port)
        ports_traced[port] = sorted(port_trace)

    candidates: set[str] = set()
    for port, traced in ports_traced.items():
        if set(traced).intersection(sync_names_set):
            candidates.add(port)

    candidates_from_syncs = set(candidates)

    candidates_after_semantic_filter = set(filter(filter_clock_candidate_semanitcly, candidates_from_syncs))

    clk_candidates = sorted(candidates_after_semantic_filter)
    print(f"Clock candidates: {clk_candidates}")

    return {
        "data_rtlil": data_rtlil,
        "data_rtlil_post_proc": data_rtlil_post_proc,
        "portlist": portlist,
        "sync_data": sync_data,
        "port_data": port_data,
        "connection_data": connection_data,
        "ports_traced": ports_traced,
        "clock_candidates": clk_candidates,
        "yosys_log": yosys_log,
    }


class ClockDetectFlow(Flow):
    flow_name: str = "clock_detect"
    flow_tags: ClassVar[list[str]] = ["hdl", "netlist", "clock"]

    def build_flow_single(self, design: dict[str, str], overwrite: bool = True) -> None:
        design_dir = self.design_dataset.designs_dir / str(design["design_name"])
        if not design_dir.exists():
            raise ValueError(f"Design directory {design_dir} does not exist, cannot build flow")
        sources_dir = design_dir / "sources"

        flow_dir = design_dir / "flows" / self.flow_name
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
        flow_dir.mkdir(parents=True, exist_ok=True)

        flow_metadata = {
            "flow_name": self.flow_name,
            "flow_tags": self.flow_tags,
        }

        flow_metadata_fp = flow_dir / "flow.json"
        flow_metadata_fp.write_text(json.dumps(flow_metadata, indent=4))

        hdl_dir = flow_dir / "hdl"
        shutil.copytree(sources_dir, hdl_dir)

        source_files_fps = [f for f in hdl_dir.iterdir() if f.is_file()]

        print(f"{design['design_name']}")

        top = auto_top(source_files_fps)
        print(f"Top module: {top}")
        clock_data = detect_clocks(source_files_fps, top_module=top, cwd=flow_dir)

        (flow_dir / "rtlil.txt").write_text(clock_data["data_rtlil"])
        (flow_dir / "rtlil_post_proc.txt").write_text(clock_data["data_rtlil_post_proc"])
        (flow_dir / "portlist.txt").write_text(clock_data["portlist"])
        (flow_dir / "port_data.json").write_text(json.dumps(clock_data["port_data"], indent=4))
        (flow_dir / "sync_data.json").write_text(json.dumps(clock_data["sync_data"], indent=4))
        (flow_dir / "connection_data.json").write_text(json.dumps(clock_data["connection_data"], indent=4))
        (flow_dir / "ports_traced.json").write_text(json.dumps(clock_data["ports_traced"], indent=4))
        (flow_dir / "clock_candidates.json").write_text(json.dumps(clock_data["clock_candidates"], indent=4))
        (flow_dir / "yosys_log.txt").write_text(clock_data["yosys_log"])

    def build_flow(self, overwrite: bool = True, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs)(delayed(self.build_flow_single)(design, overwrite=overwrite) for design in designs)
