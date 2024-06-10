from pathlib import Path

import requests
import yaml
from dotenv import dotenv_values
from github import Auth, Github

CURRENT_SCRIPT_DIR = Path(__file__).parent

env_config = dotenv_values(CURRENT_SCRIPT_DIR / ".env")
gh_token = None
if "GITHUB_TOKEN" in env_config:
    gh_token = env_config["GITHUB_TOKEN"]
if gh_token is None:
    raise ValueError("GITHUB_TOKEN not found in .env file")

if __name__ == "__main__":
    test_repo = "fusesoc/fusesoc-cores"

    g_auth = Auth.Token(gh_token)
    g = Github(auth=g_auth)
    repo = g.get_repo(test_repo)
    print(repo)

    core_results = g.search_code(
        query='"CAPI=2:" extension:core repo:fusesoc/fusesoc-cores',
    )
    print(f"Found {core_results.totalCount} .core files in {test_repo}")
    for core_result in core_results:
        download_url = core_result.download_url
        r = requests.get(download_url)
        core_data = yaml.safe_load(r.text)
        print(core_data["name"])
