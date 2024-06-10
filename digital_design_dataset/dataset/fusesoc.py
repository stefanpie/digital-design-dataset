from github import Github
from rich.pretty import pprint as pp


def get_cores_from_github_repo(owner: str, repo: str, gh_api: Github):
    items = gh_api.search_code(f"extension:.core repo:{owner}/{repo}")
    total_count = items.totalCount
    pp(f"Found {total_count} .core files in {owner}/{repo}")
    for item in items:
        print(item.name)
        print(item.path)
        print(item.url)
        print()
        # pp(item.keys())


# def get_core(owner: str, repo: str, core_fp: str, gh_api: Github):
#     # find all .core files in the repo

#     r = gh_api.search.code(f"extension:.core repo:{owner}/{repo} filename:{core}")
#     total_count = r["total_count"]
#     pp(f"Found {total_count} .core files in {owner}/{repo}")
#     items = r["items"]
#     for item in items:
#         print(item["name"])
#         print(item["path"])
#         print(item["url"])
#         print(item["score"])
#         print()
#         # pp(item.keys())
