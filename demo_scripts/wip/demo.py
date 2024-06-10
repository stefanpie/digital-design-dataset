from pathlib import Path

from digital_design_dataset.dataset.datasets import (
    EPFLDatasetRetriever,
    KoiosDatasetRetriever,
    OPDBDatasetRetriever,
    OpencoresDatasetRetriever,
    VTRDatasetRetriever,
)
from digital_design_dataset.design_dataset import (
    DesignDataset,
    ISEFlow,
    ModuleInfoFlow,
    QuartusFlow,
    YosysAIGFlow,
)

### Initialize Dataset ###

test_db_dir = Path("./test_design_dataset")
d = DesignDataset(test_db_dir, overwrite=False)

### Load Design Sources ###

retriever_opencores = OpencoresDatasetRetriever(d)
retriever_opencores.get_dataset()

retriever_vtr = VTRDatasetRetriever(d)
retriever_vtr.get_dataset()

retriever_koios = KoiosDatasetRetriever(d)
retriever_koios.get_dataset()

retriever_epfl = EPFLDatasetRetriever(d)
retriever_epfl.get_dataset()

retriever_opdb = OPDBDatasetRetriever(d)
retriever_opdb.get_dataset()

### Run Flows ###

flow_module_info = ModuleInfoFlow(d)
flow_module_info.build_flow(n_jobs=32)

flow_yosys_synth_aig = YosysAIGFlow(d)
flow_yosys_synth_aig.build_flow(n_jobs=32)

flow_ise = ISEFlow(d)  # WIP
flow_ise.build_flow(n_jobs=32)

flow_quartus = QuartusFlow(d)  # WIP
flow_quartus.build_flow(n_jobs=32)
