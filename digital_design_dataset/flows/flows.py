import json
import shutil
from typing import Any

import networkx as nx
import tqdm
from joblib import Parallel, delayed

from digital_design_dataset.design_dataset import (
    VERILOG_SOURCE_EXTENSIONS_SET,
    DesignDataset,
)
from digital_design_dataset.flows.design_hierarchy import extract_design_hierarchy
from digital_design_dataset.flows.verilog_ast import verilog_ast


class Flow:
    flow_name: str
    flow_type: str  # TODO: Change to be more like tags, like a list[str]

    def __init__(self, design_dataset: DesignDataset) -> None:
        self.design_dataset = design_dataset

    def build_flow(self, overwrite: bool = False) -> None:
        raise NotImplementedError


class LineCountFlow(Flow):
    flow_name = "line_count"
    flow_type = "text"

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        # count number of lines in a design
        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]

        lines = 0
        for source_fp in sources_fps:
            with source_fp.open() as f:
                lines += len(f.readlines())

        flow_dir = design_dir / "flows" / self.flow_name
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
        flow_dir.mkdir(parents=True, exist_ok=True)

        flow_metadata = {
            "flow_name": self.flow_name,
            "flow_type": self.flow_type,
            "num_lines": lines,
        }

        num_lines = flow_dir / "num_lines.txt"
        num_lines.write_text(str(lines))

        flow_metadata_fp = flow_dir / "flow.json"
        flow_metadata_fp.write_text(json.dumps(flow_metadata, indent=4))

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs)(
            delayed(self.build_flow_single)(design, overwrite=overwrite)
            for design in designs
        )


class ModuleInfoFlow(Flow):
    flow_name = "module_count"
    flow_type = "text"

    def __init__(self, design_dataset: DesignDataset, yosys_bin: str = "yosys") -> None:
        super().__init__(design_dataset)
        self.yosys_bin = yosys_bin

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        # count number of modules in a design
        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]

        verilog_sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]

        modules = extract_design_hierarchy(verilog_sources_fps)
        num_modules = len(modules)

        flow_dir = design_dir / "flows" / self.flow_name
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
        flow_dir.mkdir(parents=True, exist_ok=True)

        flow_metadata = {
            "flow_name": self.flow_name,
            "flow_type": self.flow_type,
            "modules": modules,
            "num_modules": num_modules,
        }

        num_modules_fp = flow_dir / "num_modules.txt"
        num_modules_fp.write_text(str(num_modules))

        modules_fp = flow_dir / "modules.txt"
        modules_fp.write_text("\n".join(modules))

        flow_metadata_fp = flow_dir / "flow.json"
        flow_metadata_fp.write_text(json.dumps(flow_metadata, indent=4))

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs)(
            delayed(self.build_flow_single)(design, overwrite=overwrite)
            for design in tqdm.tqdm(designs)
        )
        self.build_flow_single(designs[0], overwrite=overwrite)


class VeribleASTFlow(Flow):
    flow_name = "yosys_ast"
    flow_type = "graph"

    def __init__(
        self,
        design_dataset: DesignDataset,
        verible_verilog_syntax_bin: str = "verible-verilog-syntax",
    ) -> None:
        super().__init__(design_dataset)
        self.verible_verilog_syntax_bin = verible_verilog_syntax_bin

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]

        # TODO: add overwrite functionality
        flow_dir = design_dir / "flows" / self.flow_name
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
        flow_dir.mkdir(parents=True, exist_ok=True)

        design_metadata_fp = design_dir / "design.json"
        with design_metadata_fp.open() as f:
            design_metadata = json.load(f)

        if "flows" not in design_metadata:
            design_metadata["flows"] = {}

        flow_metadata = {}
        flow_metadata["flow_name"] = self.flow_name
        flow_metadata["flow_type"] = self.flow_type
        design_metadata["flows"][self.flow_name] = flow_metadata

        design_metadata_fp.write_text(json.dumps(design_metadata, indent=4))

        for source_fp in sources_fps:
            if source_fp.suffix not in VERILOG_SOURCE_EXTENSIONS_SET:
                continue
            g_ast = verilog_ast(
                source_fp,
                verible_verilog_syntax_bin=self.verible_verilog_syntax_bin,
            )
            if g_ast is None:
                raise ValueError(f"FAILED to parse {source_fp}")

            g_ast_json = nx.node_link_data(g_ast)
            g_ast_fp = flow_dir / (source_fp.stem + ".ast.json")
            g_ast_fp.write_text(json.dumps(g_ast_json, indent=4))

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs)(
            delayed(self.build_flow_single)(design, overwrite=overwrite)
            for design in designs
        )


class YosysAIGFlow(Flow):
    flow_name = "yosys_aig"
    flow_type = "graph"

    def __init__(self, design_dataset: DesignDataset, yosys_bin: str = "yosys") -> None:
        super().__init__(design_dataset)
        self.yosys_bin = yosys_bin

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]

        # TODO: add overwrite functionality
        flow_dir = design_dir / "flows" / self.flow_name
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
        flow_dir.mkdir(parents=True, exist_ok=True)

        design_metadata_fp = design_dir / "design.json"
        with design_metadata_fp.open() as f:
            design_metadata = json.load(f)

        if "flows" not in design_metadata:
            design_metadata["flows"] = {}

        flow_metadata = {}
        flow_metadata["flow_name"] = self.flow_name
        flow_metadata["flow_type"] = self.flow_type
        design_metadata["flows"][self.flow_name] = flow_metadata

        design_metadata_fp.write_text(json.dumps(design_metadata, indent=4))

        aig_graph, json_data, stat_txt, stat_json = yosys_aig(
            sources_fps,
            yosys_bin=self.yosys_bin,
        )
        aig_graph_json = nx.node_link_data(aig_graph)
        aig_graph_fp = flow_dir / "aig_graph.json"
        aig_graph_fp.write_text(json.dumps(aig_graph_json, indent=4))

        aig_yosys_json_fp = flow_dir / "aig_yosys.json"
        aig_yosys_json_fp.write_text(json.dumps(json_data, indent=4))

        stat_txt_fp = flow_dir / "stat.txt"
        stat_txt_fp.write_text(stat_txt)

        stat_json_fp = flow_dir / "stat.json"
        stat_json_fp.write_text(json.dumps(stat_json, indent=4))

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        designs = self.design_dataset.index
        Parallel(n_jobs=n_jobs, backend="loky")(
            delayed(self.build_flow_single)(design, overwrite=overwrite)
            for design in tqdm.tqdm(designs)
        )


class YosysXilinxSynthFlow(Flow):
    flow_name = "yosys_xilinx_synth"
    flow_type = "graph"

    def __init__(self, design_dataset: DesignDataset, yosys_bin: str = "yosys") -> None:
        super().__init__(design_dataset)
        self.yosys_bin = yosys_bin

    def build_flow_single(
        self,
        design: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        design_dir = self.design_dataset.designs_dir / design["design_name"]
        sources_dir = design_dir / "sources"
        sources_fps = [f for f in sources_dir.iterdir() if f.is_file()]
        sources_fps = [
            f for f in sources_fps if f.suffix in VERILOG_SOURCE_EXTENSIONS_SET
        ]


class ModuleHierarchyFlow(Flow):
    flow_name = "submodule_hierarchy"
    flow_type = "source"

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        raise NotImplementedError


class ISEFlow(Flow):
    flow_name = "ise"
    flow_type = "source"

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        raise NotImplementedError


class VivadoFlow(Flow):
    flow_name = "vivado"
    flow_type = "source"

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        raise NotImplementedError


class QuartusFlow(Flow):
    flow_name = "quartus"
    flow_type = "source"

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        raise NotImplementedError


class OpenRoadFlow(Flow):
    flow_name = "openroad"
    flow_type = "source"

    def build_flow(self, overwrite: bool = False, n_jobs: int = 1) -> None:
        raise NotImplementedError
