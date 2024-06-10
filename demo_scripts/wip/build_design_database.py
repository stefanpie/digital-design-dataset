import pathlib
import re
import shutil

from dotenv import dotenv_values

from digital_design_dataset.design_dataset import DesignDataset


def count_designs(design_dir: pathlib.Path) -> int:
    """
    Counts the number of designs in a given directory.
    """

    # recursive find all .design files
    files = list(design_dir.glob("**/.design"))
    return len(files)


def count_verilog_module_definitions(design_dir: pathlib.Path) -> int:
    """
    Counts the number of verilog definitions in a given directory.
    """

    # verilog modules definitions looks like this
    # module ...stuff... endmodule
    # match the first endmodule rather than the last, lazy matching
    module_def_pattern = re.compile(r"module.*?endmodule", re.DOTALL)
    files = []
    extensions = [".v", ".sv", ".V", ".SV", ".h", ".vh", ".svh"]
    for ext in extensions:
        files += list(design_dir.glob(f"**/*{ext}"))
    module_count = 0
    for file in files:
        module_count += len(module_def_pattern.findall(file.read_text()))

    return module_count


if __name__ == "__main__":
    current_script_dir = pathlib.Path(__file__).parent

    env_config = dotenv_values(current_script_dir / ".env")
    gh_token = env_config["GITHUB_TOKEN"]

    test_db_dir = current_script_dir / "test_dataset"
    if test_db_dir.exists():
        shutil.rmtree(test_db_dir)
    test_dataset = DesignDataset(test_db_dir, gh_token=gh_token)
    test_dataset.build_academic_dataset()

    design_count = count_designs(test_db_dir)
    print(f"# of designs: {design_count}")

    module_count = count_verilog_module_definitions(test_db_dir)
    print(f"# of verilog module definitions: {module_count}")
