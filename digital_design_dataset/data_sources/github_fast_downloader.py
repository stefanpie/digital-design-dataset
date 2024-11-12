import atexit
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path


class GithubFastDownloader:
    def __init__(
        self,
        repo_name: str,
        repo_owner: str,
        repo_branch: str | None = None,
        git_bin: str | None = "git",
    ) -> None:
        if git_bin is None:
            git_bin_match = shutil.which("git")
            if git_bin_match is None:
                raise ValueError("git binary not found in PATH")
            self.git_bin = git_bin_match
        else:
            self.git_bin = git_bin

        self.repo_name = repo_name
        self.repo_owner = repo_owner
        self.repo_url = f"https://github.com/{self.repo_owner}/{self.repo_name}.git"
        self.repo_branch = repo_branch
        self.temp_dir = tempfile.TemporaryDirectory(prefix="github_fast_downloader__")
        self.repo_dir = Path(self.temp_dir.name) / "repo"

        # Register the cleanup function for vaious terimnations
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)

    def clone_repo(self) -> None:
        if not self.repo_branch:
            self.repo_branch = self.get_default_branch()

        # Shallow clone the repository (depth=1)
        subprocess.run(
            [
                self.git_bin,
                "clone",
                "--depth",
                "1",  # shallow clone (only latest commit)
                "--branch",
                self.repo_branch,
                "--no-checkout",  # don't check out files initially
                "--filter=blob:none",  # Don't fetch file data
                self.repo_url,
                str(self.repo_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def get_default_branch(self) -> str:
        result = subprocess.run(
            [
                self.git_bin,
                "ls-remote",
                "--symref",
                self.repo_url,
                "HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        for line in result.stdout.splitlines():
            if line.startswith("ref:"):
                branch = line.split()[1].split("/")[-1]
                return branch
        raise ValueError("Unable to detect the default branch.")

    def enable_sparse_checkout(self) -> None:
        subprocess.run(
            [self.git_bin, "-C", str(self.repo_dir), "config", "core.sparseCheckout", "true"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def checkout_stuff(self, files_or_dirs: list, reset: bool = True) -> None:
        sparse_checkout_file = Path(self.repo_dir) / ".git" / "info" / "sparse-checkout"

        mode = "w" if reset else "a"
        with sparse_checkout_file.open(mode, encoding="utf-8") as f:
            for item in files_or_dirs:
                f.write(f"{item}\n")

        subprocess.run(
            [self.git_bin, "-C", str(self.repo_dir), "checkout"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def reset_sparse_checkout_list(self) -> None:
        sparse_checkout_file = Path(self.repo_dir) / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.write_text("", encoding="utf-8")

    def get_path_on_disk(self, item_path: str) -> Path:
        if not self.repo_dir.exists():
            raise ValueError("Repository directory does not exist")
        if not (self.repo_dir / item_path).exists():
            raise ValueError("File does not exist in the repository")
        return self.repo_dir / item_path

    def signal_handler(self, _signum: int, _frame: object) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        self.temp_dir.cleanup()

    def __del__(self) -> None:
        self.cleanup()

    def __enter__(self) -> "GithubFastDownloader":
        self.clone_repo()
        self.enable_sparse_checkout()
        return self

    def __exit__(self, exc_type: object, exc_val: BaseException | None, exc_tb: object) -> None:
        self.cleanup()
