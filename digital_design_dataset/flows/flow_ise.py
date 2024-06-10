import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


# Helper function to run a command and save log
def run_command(command: list[str], log_file: Path) -> int:
    with log_file.open(mode="w") as log:
        result = subprocess.run(command, stdout=log, stderr=log, check=False)
    return result.returncode


@dataclass
class ISEFlowSettings:
    synth_settings: dict | None = None
    map_settings: dict | None = None
    par_settings: dict | None = None
    bitgen_settings: dict | None = None


def flow_ise(
    verilog_files: list[Path],
    top_module: str,
    build_dir: Path,
    part_name: str,
    ise_flow_settings: ISEFlowSettings,
    ise_bin_path: Path,
):
    # Ensure build_dir exists
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Define the names of the intermediate files and final output
    top_module = Path(verilog_files[0]).stem
    ngc_file = build_dir / f"{top_module}.ngc"
    ngd_file = build_dir / f"{top_module}.ngd"
    ncd_file = build_dir / f"{top_module}.ncd"
    bit_file = build_dir / f"{top_module}.bit"
    ucf_file = (
        build_dir / f"{top_module}.ucf"
    )  # Assuming you have a UCF file for constraints

    # Step 1: Synthesize (xst)
    synth_command = [
        os.path.join(ise_bin_path, "xst"),
        "-ifn",
        f"{build_dir / 'synth.tcl'}",
    ]
    # Create a TCL script for synthesis
    synth_tcl_content = f"""
    set -tmpdir {build_dir}
    set -xsthdpdir {build_dir / "xst"}
    run
    -ifn {verilog_files[0]}  # Top-level Verilog file
    -ofn {ngc_file}
    -top {top_module}
    -p {part_name}
    """
    with open(build_dir / "synth.tcl", "w") as f:
        f.write(synth_tcl_content)

    if run_command(synth_command, build_dir / "synth.log") != 0:
        print("Synthesis failed. Check synth.log for details.")
        return

    # Step 2: Translate (ngdbuild)
    ngdbuild_command = [
        os.path.join(ise_bin_path, "ngdbuild"),
        "-uc",
        str(ucf_file),
        "-p",
        part_name,
        str(ngc_file),
        str(ngd_file),
    ]
    if run_command(ngdbuild_command, build_dir / "ngdbuild.log") != 0:
        print("NGDBuild failed. Check ngdbuild.log for details.")
        return

    # Step 3: Map (map)
    map_command = [
        os.path.join(ise_bin_path, "map"),
        "-p",
        part_name,
        "-o",
        str(ncd_file),
        str(ngd_file),
    ]
    if run_command(map_command, build_dir / "map.log") != 0:
        print("Map failed. Check map.log for details.")
        return

    # Step 4: Place and Route (par)
    par_command = [
        os.path.join(ise_bin_path, "par"),
        "-w",  # Enable warning messages
        str(ncd_file),
        str(ncd_file),
    ]
    if run_command(par_command, build_dir / "par.log") != 0:
        print("Place and Route failed. Check par.log for details.")
        return

    # Step 5: Bitstream Generation (bitgen)
    bitgen_command = [
        os.path.join(ise_bin_path, "bitgen"),
        str(ncd_file),
        str(bit_file),
    ]
    if run_command(bitgen_command, build_dir / "bitgen.log") != 0:
        print("Bitstream generation failed. Check bitgen.log for details.")
        return

    print(f"FPGA flow completed successfully. Bitstream file: {bit_file}")
