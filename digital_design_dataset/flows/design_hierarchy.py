import subprocess
import tempfile
from pathlib import Path


def extract_design_hierarchy(design_files: list[Path]) -> list[str]:
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
            raise RuntimeError(
                f"yosys exited with code {p.returncode}.\n"
                f"stdout:\n{std_out}\n"
                f"stderr:\n{std_err}",
            )
        std_out = p.stdout.decode("utf-8")

        # parse the output of the ls command
        # hierarchy_output = hierarchy_fp.read_text()
        ls_output = ls_output_fp.read_text()
        # jny_output = jny_fp.read_text()

    modules = ls_output.split("\n")[2:]
    modules = [m.strip() for m in modules]
    modules = [m for m in modules if m != ""]
    if len(list(set(modules))) != len(modules):
        raise RuntimeError("Duplicate modules found in the design hierarchy.")
    # pp(modules)

    # jny_data = json.loads(jny_output)
    # jny_data_modules = jny_data["modules"]
    # pp(jny_data_modules)
    # design_graph = nx.DiGraph()

    return modules
