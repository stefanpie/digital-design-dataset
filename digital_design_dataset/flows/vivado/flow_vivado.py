import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from joblib import Parallel, delayed
from pydantic import BaseModel, Field

from digital_design_dataset.design_dataset import VERILOG_SOURCE_EXTENSIONS_SET, DesignDataset
from digital_design_dataset.flows.decompose import compute_top_modules
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
    def auto_find_quartus_sh() -> Path:
        return get_bin("quartus_sh")


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
    ) -> None:
        super().__init__(design_dataset)
        self.part = part
        self.tool_bins = tool_bins
        self.tool_settings = tool_settings

    @staticmethod
    def check_supported_part(part: PartXilinx) -> None:
        # supported_devices = get_supported_devices_raw(ToolBinsAlteraQuartus.auto_find_quartus_sh())
        # if part.device not in supported_devices:
        #     raise ValueError(
        #         f"The specified device {part.device} is not supported by the specified Quartus installation",
        #     )
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

        top_modules = compute_top_modules(hdl_files)
        if len(top_modules) != 1:
            raise ValueError(
                f"Expected exactly one top module for design {design_name}, got {len(top_modules)} top modules: {top_modules}",
            )
        top_module = top_modules[0]

        # TODO: This script is certainly not correct
        vivado_script = ""
        vivado_script += f"create_project {design_name} -part {self.part.device} -force\n"
        for hdl_file in hdl_files:
            vivado_script += f"add_files {hdl_file.resolve()}\n"
        vivado_script += f"set_property top {top_module} [current_fileset]\n"
        vivado_script += "launch_runs synth_1\n"
        vivado_script += "wait_on_run synth_1\n"
        vivado_script += "write_checkpoint -force design__post_synth.dcp\n"
        vivado_script += "launch_runs impl_1\n"
        vivado_script += "wait_on_run impl_1\n"
        vivado_script += "write_checkpoint -force design__post_impl.dcp\n"
        vivado_script += "write_bitstream -force design.bit\n"
        vivado_script += "exit\n"

        vivado_script_fp = flow_dir / "run.tcl"
        vivado_script_fp.write_text(vivado_script)

        p_vivado = subprocess.run(
            [str(self.tool_bins.vivado), "-mode", "batch", "-source", str(vivado_script_fp)],
            capture_output=True,
            text=True,
            check=False,
        )
        check_process_output(p_vivado)
