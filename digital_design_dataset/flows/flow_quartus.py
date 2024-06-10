from dataclasses import dataclass
from pathlib import Path


@dataclass
class QuartusFlowSettings:
    quartus_settings: dict | None = None
    quartus_map_settings: dict | None = None
    quartus_fit_settings: dict | None = None
    quartus_asm_settings: dict | None = None
    quartus_sta_settings: dict | None = None
    quartus_pgm_settings: dict | None = None


def flow_quartus(
    verilog_files: list[Path],
    top_module: str,
    build_dir: Path,
    part_name: str,
    quartus_flow_settings: QuartusFlowSettings,
    quartus_bin_path: Path,
): ...
