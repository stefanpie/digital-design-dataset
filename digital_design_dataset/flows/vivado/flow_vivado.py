import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from joblib import Parallel, delayed
from pydantic import BaseModel, Field

from digital_design_dataset.design_dataset import VERILOG_SOURCE_EXTENSIONS_SET, DesignDataset
from digital_design_dataset.flows.decompose import (
    auto_top,
    compute_hierarchy_redundent,
    compute_top_modules,
    get_top_nodes,
)
from digital_design_dataset.flows.flow_tools import check_process_output, get_bin
from digital_design_dataset.flows.flows import Flow
from digital_design_dataset.logger import build_logger


class PartXilinx(BaseModel):
    device: str
    family: str = ""
    package: str = ""
    speed: str = ""


class ToolBinsXilinxVivado(BaseModel):
    vivado: Path

    @classmethod
    def auto_find_bins(cls) -> "ToolBinsXilinxVivado":
        return cls(
            vivado=get_bin("vivado"),
        )

    @staticmethod
    def auto_find_vivado() -> Path:
        return get_bin("vivado")


class FlowSettingsXilinxVivado(BaseModel):
    additional_settings: list[str] = Field(default_factory=list)
    additional_constraints: list[str] = Field(default_factory=list)
    vivado_opts: list[str] = Field(default_factory=list)
    n_cores: int = 1


class XilinxVivadoFlow(Flow):
    flow_name: str = "xilinx_vivado_flow"
    flow_tags: ClassVar[list[str]] = ["xilinx", "vivado", "synthesis", "implementation"]

    def __init__(
        self,
        design_dataset: DesignDataset,
        part: PartXilinx,
        tool_bins: ToolBinsXilinxVivado,
        tool_settings: FlowSettingsXilinxVivado,
        auto_top: bool = True,
    ) -> None:
        super().__init__(design_dataset)
        self.part = part
        self.tool_bins = tool_bins
        self.tool_settings = tool_settings
        self.auto_top = auto_top

    @staticmethod
    def check_supported_part(part: PartXilinx) -> None:
        raise NotImplementedError

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs, backend="loky")(
            delayed(self.build_flow_single)(design, overwrite=overwrite) for design in tqdm.tqdm(designs)
        )

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        logger = build_logger("ModuleInfoFlow", logging.INFO)
        logger.info(f"Building flow {self.flow_name} for {design['design_name']}")

        design_dir = self.design_dataset.designs_dir / str(design["design_name"])
        if not design_dir.exists():
            raise ValueError(f"Design directory {design_dir} does not exist, cannot build flow")
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

        top_module = None
        g_hier = compute_hierarchy_redundent(hdl_files)
        top_nodes = get_top_nodes(g_hier)
        if len(top_nodes) != 1:
            match self.auto_top:
                case True:
                    top_module = auto_top(hdl_files)
                case False:
                    raise ValueError(
                        f"Expected exactly one top module for design {design_name}, got {len(top_nodes)} top modules: {top_nodes}",
                    )
        else:
            top_module = top_nodes[0]

        if top_module is None:
            raise ValueError(f"Issues with top module detection logic for design {design_name}")

        vivado_script = ""

        vivado_script += f"create_project {design_name} -part {self.part.device} -force\n"
        for hdl_file in hdl_files:
            vivado_script += f"add_files {hdl_file.resolve()}\n"
        vivado_script += f"set_property top {top_module} [current_fileset]\n"

        # Synthesis step
        vivado_script += "launch_runs synth_1\n"
        vivado_script += "wait_on_run synth_1\n"
        vivado_script += "open_run synth_1\n"
        vivado_script += "write_checkpoint -force design__post_synth.dcp\n"

        # Generate synthesis reports
        vivado_script += "report_timing_summary -file timing_report_synth.rpt\n"
        vivado_script += "report_utilization -file utilization_report_synth.rpt\n"
        vivado_script += "report_power -file power_report_synth.rpt\n"

        # Implementation step
        vivado_script += "launch_runs impl_1\n"
        vivado_script += "wait_on_run impl_1\n"
        vivado_script += "open_run impl_1\n"
        vivado_script += "write_checkpoint -force design__post_impl.dcp\n"

        # Generate implementation reports
        vivado_script += "report_timing_summary -file timing_report_impl.rpt\n"
        vivado_script += "report_utilization -file utilization_report_impl.rpt\n"
        vivado_script += "report_power -file power_report_impl.rpt\n"

        # Optional: Write bitstream if needed
        # vivado_script += "write_bitstream -force design.bit\n"

        vivado_script += "exit\n"

        vivado_script_fp = flow_dir / "run.tcl"
        vivado_script_fp.write_text(vivado_script)

        p_vivado = subprocess.run(
            [str(self.tool_bins.vivado), "-mode", "batch", "-source", str(vivado_script_fp)],
            capture_output=True,
            text=True,
            check=False,
            cwd=flow_dir,
        )
        check_process_output(p_vivado)
