from pathlib import Path

from digital_design_dataset.data_sources.github_fast_downloader import GithubFastDownloader


def test_github_fast_downloader_simple() -> None:
    gfd = GithubFastDownloader(
        "vtr-verilog-to-routing",
        "verilog-to-routing",
    )

    gfd.clone_repo()
    gfd.enable_sparse_checkout()
    gfd.checkout_stuff(
        [
            "vtr_flow/benchmarks/fpu",
        ],
        reset=False,
    )
    assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "fpu").exists()

    gfd.checkout_stuff(
        [
            "vtr_flow/benchmarks/blif",
            "vtr_flow/benchmarks/vexriscv/VexRiscvSmallest.v",
        ],
        reset=False,
    )
    assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "blif").exists()
    assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "fpu").exists()
    assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "vexriscv" / "VexRiscvSmallest.v").exists()

    gfd.reset_sparse_checkout_list()

    gfd.checkout_stuff(
        [
            "vtr_flow/benchmarks/fpu",
        ],
        reset=False,
    )
    assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "fpu").exists()
    assert not (gfd.repo_dir / "vtr_flow" / "benchmarks" / "blif").exists()
    assert not (gfd.repo_dir / "vtr_flow" / "benchmarks" / "vexriscv" / "VexRiscvSmallest.v").exists()

    gfd.reset_sparse_checkout_list()
    gfd.checkout_stuff([])

    stuff_in_dir = list(gfd.repo_dir.iterdir())
    assert len(stuff_in_dir) == 1
    assert stuff_in_dir[0].name == ".git"

    gfd.cleanup()

    assert not Path(gfd.temp_dir.name).exists()
    assert not gfd.repo_dir.exists()


def test_github_fast_downloader_context_manager() -> None:
    temp_dir_path = None
    repo_dir_path = None

    with GithubFastDownloader(
        "vtr-verilog-to-routing",
        "verilog-to-routing",
    ) as gfd:
        temp_dir_path = Path(gfd.temp_dir.name)
        repo_dir_path = gfd.repo_dir

        gfd.checkout_stuff(
            ["vtr_flow/benchmarks/fpu"],
        )
        assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "fpu").exists()

        gfd.checkout_stuff(
            ["vtr_flow/benchmarks/blif", "vtr_flow/benchmarks/vexriscv/VexRiscvSmallest.v"],
            reset=False,
        )
        assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "blif").exists()
        assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "fpu").exists()
        assert (gfd.repo_dir / "vtr_flow" / "benchmarks" / "vexriscv" / "VexRiscvSmallest.v").exists()

        gfd.reset_sparse_checkout_list()
        gfd.checkout_stuff([])
        stuff_in_dir = list(gfd.repo_dir.iterdir())
        assert len(stuff_in_dir) == 1
        assert stuff_in_dir[0].name == ".git"

    assert not temp_dir_path.exists()
    assert not repo_dir_path.exists()
