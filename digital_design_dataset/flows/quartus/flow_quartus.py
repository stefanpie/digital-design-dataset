import json
import logging
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import jinja2
import psutil
import tqdm
from joblib import Parallel, delayed
from pydantic import BaseModel, Field

from digital_design_dataset.design_dataset import VERILOG_SOURCE_EXTENSIONS_SET, DesignDataset
from digital_design_dataset.flows.decompose import compute_top_modules
from digital_design_dataset.flows.flow_tools import MeasureTime, check_process_output, get_bin
from digital_design_dataset.flows.flows import Flow
from digital_design_dataset.logger import build_logger


def tcl_quote(string: str) -> str:
    escaped = '"' + re.sub(r"([$[\\])", r"\\\1", string) + '"'
    return escaped


class ToolBinsAlteraQuartus(BaseModel):
    quartus_sh: Path
    quartus_map: Path
    quartus_fit: Path
    quartus_asm: Path
    quartus_sta: Path

    @classmethod
    def auto_find_bins(cls) -> "ToolBinsAlteraQuartus":
        return cls(
            quartus_sh=get_bin("quartus_sh"),
            quartus_map=get_bin("quartus_map"),
            quartus_fit=get_bin("quartus_fit"),
            quartus_asm=get_bin("quartus_asm"),
            quartus_sta=get_bin("quartus_sta"),
        )

    @staticmethod
    def auto_find_quartus_sh() -> Path:
        return get_bin("quartus_sh")


class FlowSettingsAlteraQuartus(BaseModel):
    additional_settings: list[str] = Field(default_factory=list)
    additional_constraints: list[str] = Field(default_factory=list)
    quartus_sh_opts: list[str] = Field(default_factory=list)
    quartus_map_opts: list[str] = Field(default_factory=list)
    quartus_fit_opts: list[str] = Field(default_factory=list)
    quartus_asm_opts: list[str] = Field(default_factory=list)
    quartus_sta_opts: list[str] = Field(default_factory=list)
    n_cores: int = 1


class PartAltera(BaseModel):
    device: str
    family: str = ""
    package: str = ""
    speed: str = ""


def get_supported_devices_raw(bin_quartus_sh: Path) -> list[str]:
    p_args = [
        str(bin_quartus_sh),
        "--tcl_eval",
        "get_part_list",
    ]
    p = subprocess.run(p_args, capture_output=True, text=True, check=True)
    check_process_output(p)
    parts = p.stdout.strip().split()
    return parts


class AlteraQuartusFlow(Flow):
    flow_name: str = "altera_quartus_flow"
    flow_tags: ClassVar[list[str]] = ["altera", "quartus", "synthesis", "implementation"]

    def __init__(
        self,
        design_dataset: DesignDataset,
        part: PartAltera,
        tool_bins: ToolBinsAlteraQuartus,
        tool_settings: FlowSettingsAlteraQuartus,
    ) -> None:
        super().__init__(design_dataset)
        self.part = part
        self.tool_bins = tool_bins
        self.tool_settings = tool_settings

    @staticmethod
    def check_supported_part(part: PartAltera) -> None:
        supported_devices = get_supported_devices_raw(ToolBinsAlteraQuartus.auto_find_quartus_sh())
        if part.device not in supported_devices:
            raise ValueError(
                f"The specified device {part.device} is not supported by the specified Quartus installation",
            )

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        logger = build_logger("ModuleInfoFlow", logging.INFO)
        logger.info(f"Building flow {self.flow_name} for {design['design_name']}")

        design_dir = self.design_dataset.designs_dir / str(design["design_name"])
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
        hdl_files = [f for f in source_files_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]

        design_name = design["design_name"]

        top_modules = compute_top_modules(hdl_files)
        if len(top_modules) != 1:
            raise ValueError(
                f"Expected exactly one top module for design {design_name}, got {len(top_modules)} top modules: {top_modules}",
            )
        top_module = top_modules[0]

        project_setup_script = jinja2.Template(
            """
            project_new {{ design_name }} -overwrite

            set_global_assignment -name NUM_PARALLEL_PROCESSORS {{ settings.n_cores }}

            set_global_assignment -name DEVICE {{ part.device }}

            {% for file in hdl_files %}
            {% if file.suffix == ".v" %}
                set_global_assignment -name VERILOG_FILE {{ file }}
            {% elif file.suffix == ".sv" %}
                set_global_assignment -name SYSTEMVERILOG_FILE {{ file }}
            {% endif %}
            {% endfor %}
            set_global_assignment -name TOP_LEVEL_ENTITY {{ top_module }}

            # set_global_assignment -name GENERATE_RBF_FILE ON

            {% for setting in settings.additional_settings %}
            {{ setting }}
            {% endfor %}
            """,
        ).render(
            design_name=design["design_name"],
            hdl_files=hdl_files,
            top_module=top_module,
            part=self.part,
            settings=self.tool_settings,
        )
        project_setup_script_fp = flow_dir / "project_setup.tcl"
        project_setup_script_fp.write_text(project_setup_script)

        sdc_txt = jinja2.Template(
            """
            {% for constraint in settings.additional_constraints %}
            {{ constraint }}
            {% endfor %}
            """,
        ).render(settings=self.tool_settings)
        sdc_fp = flow_dir / "constraints.sdc"
        sdc_fp.write_text(sdc_txt)

        # quartus_sh
        logger.info("Running quartus_sh to setup project")
        p_args__quartus_sh = [
            str(self.tool_bins.quartus_sh),
            "-t",
            str(project_setup_script_fp),
        ]
        with MeasureTime() as mt:
            p__quartus_sh = subprocess.run(
                p_args__quartus_sh,
                capture_output=True,
                text=True,
                check=False,
                cwd=flow_dir,
            )
        check_process_output(p__quartus_sh)
        stage_data = {
            "stage": "quartus_sh",
            "duration": mt.elapsed_time,
            "stdout": p__quartus_sh.stdout,
            "stderr": p__quartus_sh.stderr,
        }

        # quartus_map
        logger.info("Running quartus_map")
        p_args__quartus_map = [
            str(self.tool_bins.quartus_map),
            design["design_name"],
            *self.tool_settings.quartus_map_opts,
        ]
        p__quartus_map = subprocess.run(p_args__quartus_map, capture_output=True, text=True, check=False, cwd=flow_dir)
        check_process_output(p__quartus_map)

        # quartus_fit
        logger.info("Running quartus_fit")
        p_args__quartus_fit = [
            str(self.tool_bins.quartus_fit),
            design["design_name"],
            *self.tool_settings.quartus_fit_opts,
        ]
        p__quartus_fit = subprocess.run(p_args__quartus_fit, capture_output=True, text=True, check=False, cwd=flow_dir)
        check_process_output(p__quartus_fit)

        # quartus_asm
        logger.info("Running quartus_asm")
        p_args__quartus_asm = [
            str(self.tool_bins.quartus_asm),
            design["design_name"],
            *self.tool_settings.quartus_asm_opts,
        ]
        p__quartus_asm = subprocess.run(p_args__quartus_asm, capture_output=True, text=True, check=False, cwd=flow_dir)
        check_process_output(p__quartus_asm)

        # # quartus_sta
        # logger.info("Running quartus_sta")
        # p_args__quartus_sta = [
        #     str(self.tool_bins.quartus_sta),
        #     design["design_name"],
        #     *self.tool_settings.quartus_sta_opts,
        # ]
        # p__quartus_sta = subprocess.run(p_args__quartus_sta, capture_output=True, text=True, check=False, cwd=flow_dir)
        # check_process_output(p__quartus_sta)

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs, backend="loky")(
            delayed(self.build_flow_single)(design, overwrite=overwrite) for design in tqdm.tqdm(designs)
        )
