from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpenROADFlowSettings: ...


def flow_openroad(
    verilog_files: list[Path],
    top_module: str,
    build_dir: Path,
    openroad_flow_settings: OpenROADFlowSettings,
    openroad_bin_path: Path,
): ...
