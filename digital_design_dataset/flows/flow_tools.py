import json
import shutil
import subprocess
from pathlib import Path


def get_bin(prog_name: str) -> Path:
    match_which = shutil.which(prog_name)
    if match_which is None:
        raise FileNotFoundError(f"{prog_name} not found in PATH")
    bin_prog = Path(match_which)

    return bin_prog


def get_bin_yosys() -> Path:
    return get_bin("yosys")


def check_process_output(process: subprocess.CompletedProcess) -> None:
    if process.returncode != 0:
        raise RuntimeError(
            f"Process returned non-zero exit code: {process.returncode}\n"
            f"stdout: {process.stdout}\n"
            f"stderr: {process.stderr}",
        )


class SimpleTextWriter:
    def __init__(self) -> None:
        self.text = ""
        self.indent_level = 0
        self.indent_str = " " * 4

    def write(self, s: str) -> None:
        self.text += self.indent_str * self.indent_level + s

    def writeline(self, s: str) -> None:
        self.text += self.indent_str * self.indent_level + s + "\n"

    def writenewline(self) -> None:
        self.text += "\n"

    def indent(self) -> None:
        self.indent_level += 1

    def dedent(self) -> None:
        self.indent_level -= 1

    def __str__(self) -> str:
        return self.text
