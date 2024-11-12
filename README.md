# Large Scale Digital Design Dataset

This project aims to build the largest collection of digital hardware design sources. This includes collecting public sources, writing scripts for automated fetching, preprocessing design sources into a common structure, checking for HDL syntax correctness, and verifying synthesizability. This project also aims to provide a generic extendable API for wiring custom flows for user-defined feature extraction and running external tools to generate more associated design data. The hope is that the presented dataset will be productive for EDA research, including benchmarking and deep learning research.

This is an active project so parts are not full complete or polished yet.

## Contact

This work is pursued by Stefan Abi-Karam ([stefanabikaram@gatech.edu](mailto:stefanabikaram@gatech.edu), [stefanabikaram.com](https://stefanabikaram.com)) as an extension of his research work for his PhD in Electrical and Computer Engineering at Georgia Tech, as well as his research at the Georgia Tech Research Institute (GTRI). Please feel free to reach out if you are interested or have any questions.

## Status

✅: Completed, 🏗️: Activly In-Progress, 〰️: Planned

### Dataset Sources

- ✅ OS - OpenCores / FreeCores (hand-curated subset, ~126 designs)
- 〰️ OS - BlackParrot
- 〰️ OS - MemPool
- 〰️ OS - NVDLA
- 〰️ OS - CVA6
- 〰️ OS - Vortex GPGPU
- 🏗️ OS - FPNew
- 🏗️ OS - SERV Core
- 〰️ OS - LiteX SoC Ecosystem
- 〰️ OS - PicoRV32
- 〰️ OS - OpenTitan
- 🏗️ OS - FuseSoC Core Library
- 🏗️ OS - secworks Core Library
- 〰️ OS - MLBlocks
- 〰️ OS - PULP Cores and Libraries
- 〰️ OS - GRLIB IP Library
- ✅ OS - DeepBenchVerilog
- ✅ OS - tangxifan/micro\_benchmark
- 〰️ OS - UT-LCA/tpu\_like\_design
- 〰️ OS - UT-LCA/tpu\_v2
- 〰️ OS - UT-LCA/brainwave-like-design
- ✅ OS - mongrelgem/Verilog-Adder
- 〰️ OS - taneroksuz/fpu
- 〰️ OS - alexforencich/* Cores
<br>
- ✅ Bench - HW2VEC
- ✅ Bench - OpenPiton Design Benchmark
- ✅ Bench - Verilog to Routing (VTR)
- ✅ Bench - Koios 2.0
- 🏗️ Bench - Titan 2.0
- ✅ Bench - MCNC 20
- ✅ Bench - ISCAS 85
- ✅ Bench - ISCAS 89
- ✅ Bench - LGSynth 89
- ✅ Bench - LGSynth 91
- ✅ Bench - IWLS 93
- ✅ Bench - I99T (ITC 99 subset)
- 🏗️ Bench - IWLS 2005: Faraday Subset
- 🏗️ Bench - IWLS 2005: Gaisler Subset
- ✅ Bench - EPFL Combinational Benchmark
- 🏗️ Bench - HDLBits / VerilogEval Subset
<br>
- ✅ HLS - PolyBench
- 🏗️ HLS - Machsuite
- 🏗️ HLS - Rosetta
- 🏗️ HLS - CHStone
- 🏗️ HLS - Rodina
- 🏗️ HLS - Parallel Programming For FPGAs
- 🏗️ HLS - Xilinx/Vitis-HLS-Introductory-Examples
<br>
- ✅ Exp - Regex State Machines
- 〰️ Exp - Scraped Efabless Submissions
<br>
- 〰️ DSL / Arch - PGRA
- 〰️ DSL / Arch - OpenFPGA
- 〰️ DSL / Arch - FloPoCo
<br>
- ✅ Demo - Espresso PLA
- ✅ Demo - XACT Designs

OS: Open Source, Bench: Benchmark, HLS: High Level Synthesis, Exp: Experiment, DSL / Arch: Domain Specific Language and Architecture Generators

Note 1: Since we define Verilog as our based HDL, we must translate some sources from formats like VHDL or BLIF into Verilog. This includes cases like the Titan benchmarks and the GRLIB IP library. Somtimes this also includes building tools to translate older scarcely documented formats like PLA and XNF. This is the case for the Espresso PLA demo and the XACT designs.

Note 2: For HLS based sources, we can use different HLS tools for different versions of the source. To begin with, we will use Vitis HLS. Other HLS tools include Intel HLS Compiler, Microchip's SmartHLS, Bambu, and Dynamatic.

### Flows

- ✅ Verible - AST / CST
- ✅ Yosys - Module Listing
- ✅ Yosys - Module Hierarchy
- ✅ Yosys - Auto Top Module Identification
- ✅ Yosys - Generic Synthesis / AIG (using `synth` + `aigmap`)
- 🏗️ Yosys - Xilinx Synthesis + Techmap
- 🏗️ ISE - Synth + PnR
- 〰️ Vivado - Synth + PnR
- ✅ Quartus - Synth + PnR
- 〰️ OpenROAD

There is an explicit focus on FPGA tools as an initial priority since the active research this project is part of is focused on EDA flows for FPGAs.

### Licensing Verification

Part of this project involves verifying the license status or chain of licensing for each included source in order to accurately present this information for all sources. This is a complex task because many sources are derived from others without explicit licensing information, have non-standard licenses, or lack proper attribution. This is a work in progress.

Our current goal is to release the dataset under a non-copyleft license. Consequently, we cannot include any sources that are licensed with a copyleft license. We are presently working on tracking and verifying the licenses of all sources and further refining the dataset to ensure it can be release under a non-copyleft license. As the dataset construction code and API is a core part of this work, we also aim to provide users with clear documentation on how to reproducibly rebuild the dataset. This will enable end users to incorporate copyleft sources into their own work if they wish without redistributing them directly.
