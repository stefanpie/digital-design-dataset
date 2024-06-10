import json
import subprocess
import tempfile
from pathlib import Path


def yosys_synth_xilinx(verilog_file: Path) -> str:
    synth_xilinx_temp_file = tempfile.NamedTemporaryFile(suffix=".synth_xilinx.json")

    script = ""
    script += f"read_verilog {verilog_file};\n"
    script += "hierarchy -check -auto-top;\n"
    script += "synth_xilinx;\n"
    script += f"write_json {synth_xilinx_temp_file.name};\n"

    p = subprocess.run(
        ["yosys", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"yosys_synth_xilinx failed with return code {p.returncode}:\n{p.stderr}",
        )

    json_raw = synth_xilinx_temp_file.read().decode().strip()
    synth_xilinx_temp_file.close()
    json_data = json.loads(json_raw)

    return json_data
