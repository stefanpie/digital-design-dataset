import csv
from math import ceil
from pathlib import Path

import requests
from rich.pretty import pprint as pt


def data_to_csv(data: list[dict], fp: Path) -> None:
    keys = data[0].keys()
    with open(fp, "w") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def get_num_verilog_repos(gh_token: str | None = None) -> int:
    """
    Get the number of repos with verilog or systemverilog files.
    """

    q = "language:verilog+language:systemverilog"
    per_page = 100
    url = f"https://api.github.com/search/repositories?q={q}&per_page={per_page}"
    if gh_token is not None:
        headers = {"Authorization": f"Bearer {gh_token}"}

    # make the request
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        data = r.json()
    else:
        raise Exception(f"Error: {r.status_code}")
    num_repos = data["total_count"]
    return num_repos


def search_verilog_repos(page=1, gh_token: str | None = None) -> dict:
    """
    Search all repos on github with verilog files.
    """

    q = "language:verilog+language:systemverilog"
    per_page = 100
    url = f"https://api.github.com/search/repositories?q={q}&page={page}&per_page={per_page}"
    if gh_token is not None:
        headers = {"Authorization": f"Bearer {gh_token}"}
    else:
        headers = {}

    # make the request
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        data = r.json()
    else:
        print(f"Error: {r.status_code}")
        pt(r.text)
        raise Exception(f"Request failed with status code: {r.status_code}")
    return data


def process_search_data(data: dict) -> list:
    """
    Process the search data from github.
    """
    repo_list_data = data["items"]
    # for each dict in the list extract the "id", "full_name" and "html_url"
    # keys and add them to a new list
    mapped_repo_list_data = []
    for repo in repo_list_data:
        mapped_repo_list_data.append(
            {
                "id": repo["id"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
            },
        )
    return mapped_repo_list_data


def index_all_verilog_repos(
    database_dir: Path,
    num_pages: int | None = None,
    gh_token: str | None = None,
) -> list:
    """
    Search all repos on github with verilog or systemverilog files.
    """

    index_dir = database_dir / "github" / "index"
    if not index_dir.exists():
        index_dir.mkdir(parents=True, exist_ok=True)

    repos_per_page = 100
    num_total_repos = get_num_verilog_repos(gh_token=gh_token)
    num_total_pages = int(ceil(num_total_repos / repos_per_page))

    print(f"Total number of repos: {num_total_repos}")
    print(f"Total number of pages: {num_total_pages}")

    pages_to_fetch = None
    if num_pages is not None:
        pages_to_fetch = num_pages
    else:
        pages_to_fetch = num_total_pages

    print(f"Fetching {pages_to_fetch} pages")

    for page in range(1, pages_to_fetch + 1):
        print(f"Fetching page: {page}")
        print(f"Percent complete: {(page / pages_to_fetch) * 100}%")
        print(
            f"Percent of total repos: {(page * repos_per_page / num_total_repos) * 100}%",
        )
        page_data = search_verilog_repos(page=page, gh_token=gh_token)
        processed_page_data = process_search_data(page_data)
        data_to_csv(processed_page_data, index_dir / f"{page}.csv")

    index_fps = [index_dir / f"{page}.csv" for page in range(1, pages_to_fetch + 1)]
    repo_data = []
    for index_fp in index_fps:
        with open(index_fp) as index_file:
            index_reader = csv.DictReader(index_file)
            for row in index_reader:
                repo_data.append(row)
    return repo_data


def retrive_single_repo_data(
    repo_id: str,
    gh_token: str | None = None,
) -> list[dict]:
    url = f"https://api.github.com/repos/{repo_id}"
    if gh_token is not None:
        headers = {"Authorization": f"Bearer {gh_token}"}

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
    else:
        print(f"Error: {r.status_code}")
        pt(r.text)
        raise Exception(f"Request failed with status code: {r.status_code}")
    # pt(data)
    return data
