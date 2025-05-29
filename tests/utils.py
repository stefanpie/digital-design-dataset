from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass
class CommonTestEnvVars:
    gh_token: str | None
    test_path: Path
    n_jobs: int

    @classmethod
    def from_env_file(cls, env_fp: Path) -> "CommonTestEnvVars":
        gh_token, test_path, n_jobs = load_common_test_env_vars(env_fp)
        return cls(gh_token=gh_token, test_path=test_path, n_jobs=n_jobs)


def load_common_test_env_vars(env_fp: Path) -> tuple[str | None, Path, int]:
    env_config = dotenv_values(env_fp)

    # load github token
    gh_token = None
    if "GITHUB_TOKEN" in env_config:
        gh_token = env_config["GITHUB_TOKEN"]

    # load test path
    if "TEST_DIR" not in env_config:
        raise ValueError("TEST_DIR not defined in .env file")
    test_path_val = env_config["TEST_DIR"]
    if not test_path_val:
        raise ValueError("TEST_DIR not defined in .env file")
    test_path = Path(test_path_val)

    # load n_jobs
    if "N_JOBS" not in env_config:
        raise ValueError("N_JOBS not defined in .env file")
    n_jobs_val = env_config["N_JOBS"]
    if not n_jobs_val:
        raise ValueError("N_JOBS not defined in .env file")
    try:
        n_jobs = int(n_jobs_val)
    except ValueError as e:
        raise ValueError("N_JOBS must be an integer") from e
    if n_jobs < 1:
        raise ValueError("N_JOBS must be greater than 0")

    return (gh_token, test_path, n_jobs)
