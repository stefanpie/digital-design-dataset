import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

import jinja2
from joblib import Parallel, delayed

from digital_design_dataset.design_dataset import VERILOG_SOURCE_EXTENSIONS_SET, DesignDataset
from digital_design_dataset.flows.flows import Flow
from digital_design_dataset.logger import build_logger


class YosysUserDefinedFlow(Flow):
    flow_name: str = "yosys_user_defined"
    flow_tags: ClassVar[list[str]] = ["user_defined"]

    def __init__(
        self,
        design_dataset: DesignDataset,
        yosys_bin: str = "yosys",
        script_template: str | jinja2.Template | None = None,
    ) -> None:
        super().__init__(design_dataset)
        self.yosys_bin = yosys_bin
        if isinstance(script_template, str):
            self.script_template = jinja2.Template(script_template)
        elif isinstance(script_template, jinja2.Template):
            self.script_template = script_template
        else:
            self.script_template = jinja2.Template("")

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        logger = build_logger("YosysUserDefinedFlow", logging.INFO)
        logger.info(f"Building flow {self.flow_name} for {design['design_name']}")

        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]

        verilog_sources_fps = [f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET]

        yosys_script_rendered = self.script_template.render(
            design=design,
            sources_fps=verilog_sources_fps,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            ys_script_fp = Path(tmpdir) / "script.ys"
            ys_script_fp.write_text(yosys_script_rendered)

            p = subprocess.run(
                [self.yosys_bin, "-s", str(ys_script_fp)],
                capture_output=True,
                check=False,
            )

            if p.returncode != 0:
                std_out = p.stdout.decode("utf-8")
                std_err = p.stderr.decode("utf-8")
                logger.error(
                    f"Yosys call to extract design hierarchy "
                    f" failed with code {p.returncode}.\n"
                    f"design_files: {verilog_sources_fps}"
                    f"stdout:\n{std_out}\n"
                    f"stderr:\n{std_err}",
                )
                raise RuntimeError(
                    f"yosys exited with code {p.returncode}.\nstdout:\n{std_out}\nstderr:\n{std_err}",
                )

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs)(delayed(self.build_flow_single)(design, overwrite=overwrite) for design in designs)
