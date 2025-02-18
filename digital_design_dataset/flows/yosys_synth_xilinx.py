import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from networkx.classes.digraph import DiGraph

from digital_design_dataset.flows.connectivity_table import parse_connectivity_table


def yosys_synth_xilinx(
    verilog_files: list[Path],
    flow_dir: Path,
    yosys_bin: str = "yosys",
) -> tuple[str, DiGraph, Any, str, str, str, Any]:
    connectivity_table_temp_file = tempfile.NamedTemporaryFile(suffix=".txt")
    json_temp_file = tempfile.NamedTemporaryFile(suffix=".json")
    verilog_temp_file = tempfile.NamedTemporaryFile(suffix=".v")
    stat_temp_file = tempfile.NamedTemporaryFile(suffix=".stat")
    stat_json_temp_file = tempfile.NamedTemporaryFile(suffix=".stat.json")
    rtlil_pre_temp_file = tempfile.NamedTemporaryFile(suffix=".rtlil")
    rtlil_temp_file = tempfile.NamedTemporaryFile(suffix=".rtlil")

    log_fp = flow_dir / "yosys_log.txt"

    script = ""
    for verilog_file in verilog_files:
        # script += f"read_verilog -nomem2reg {verilog_file};\n"  # noqa: ERA001
        script += f"read_verilog {verilog_file};\n"
    script += "hierarchy -check -auto-top;\n"
    script += f"write_rtlil {rtlil_pre_temp_file.name};\n"
    script += "synth_xilinx -family xc7;\n"
    script += "opt; clean;\n"
    script += f"write_table {connectivity_table_temp_file.name};\n"
    script += f"write_json {json_temp_file.name};\n"
    script += f"write_verilog {verilog_temp_file.name};\n"
    script += f"write_rtlil {rtlil_temp_file.name};\n"
    script += f"tee -o {stat_temp_file.name} stat;\n"
    script += f"tee -o {stat_json_temp_file.name} stat -json;\n"

    p = subprocess.run(
        [yosys_bin, "-q", "-p", script, "-l", log_fp],
        capture_output=True,
        text=True,
        check=False,
        bufsize=-1,
    )
    if p.returncode != 0:
        raise RuntimeError(
            f"Yosys failed with return code: {p.returncode}\nstdout: {p.stdout}\nstderr: {p.stderr}",
        )

    rtlil_pre_raw = rtlil_pre_temp_file.read().decode().strip()
    rtlil_pre_temp_file.close()

    connectivity_table_raw = connectivity_table_temp_file.read().decode().strip()
    connectivity_table_temp_file.close()
    graph = parse_connectivity_table(connectivity_table_raw)

    json_raw = json_temp_file.read().decode().strip()
    json_temp_file.close()
    json_data = json.loads(json_raw)

    verilog_raw = verilog_temp_file.read().decode().strip()
    verilog_temp_file.close()

    rtlil_raw = rtlil_temp_file.read().decode().strip()
    rtlil_temp_file.close()

    stat_raw = stat_temp_file.read().decode().strip()
    stat_temp_file.close()

    stat_json_raw = stat_json_temp_file.read().decode().strip()
    stat_json_temp_file.close()
    stat_json_data = json.loads(stat_json_raw)

    return (
        rtlil_pre_raw,
        graph,
        json_data,
        verilog_raw,
        rtlil_raw,
        stat_raw,
        stat_json_data,
    )
