import logging
import subprocess
import tempfile
from pathlib import Path

from digital_design_dataset.logger import build_logger


def extract_design_hierarchy(design_files: list[Path]) -> list[str]:
    logger = build_logger("extract_design_hierarchy", logging.INFO)

    modules = []

    # call yosys to read the design files and extract the design hierarchy
    with tempfile.TemporaryDirectory() as tmpdir:
        ys_script_fp = Path(tmpdir) / "script.ys"
        ys_script = ""

        for design_file in design_files:
            ys_script += f"read_verilog {design_file}\n"

        hierarchy_fp = Path(tmpdir) / "hierarchy.txt"
        ys_script += f"tee -o {hierarchy_fp} hierarchy\n"

        ls_output_fp = Path(tmpdir) / "ls_output.txt"
        ys_script += f"tee -o {ls_output_fp} ls\n"

        jny_fp = Path(tmpdir) / "jny.json"
        ys_script += f"write_jny {jny_fp}\n"

        ys_script_fp.write_text(ys_script)

        p = subprocess.run(
            ["yosys", "-s", str(ys_script_fp)],
            capture_output=True,
            check=False,
        )

        if p.returncode != 0:
            std_out = p.stdout.decode("utf-8")
            std_err = p.stderr.decode("utf-8")
            logger.error(
                f"Yosys call to extract design hierarchy "
                f" failed with code {p.returncode}.\n"
                f"design_files: {design_files}"
                f"stdout:\n{std_out}\n"
                f"stderr:\n{std_err}",
            )
            raise RuntimeError(
                f"yosys exited with code {p.returncode}.\nstdout:\n{std_out}\nstderr:\n{std_err}",
            )
        std_out = p.stdout.decode("utf-8")

        # parse the output of the ls command
        # hierarchy_output = hierarchy_fp.read_text()
        ls_output = ls_output_fp.read_text()
        # jny_output = jny_fp.read_text()

    modules = ls_output.split("\n")[2:]
    modules = [m.strip() for m in modules]
    modules = [m for m in modules if m]
    if len(list(set(modules))) != len(modules):
        raise RuntimeError("Duplicate modules found in the design hierarchy.")

    return modules
