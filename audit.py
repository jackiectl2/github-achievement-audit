#!/usr/bin/env python3
"""Read-only GitHub profile signals for people tracking Achievements.

GitHub has no public Achievement counter API. This tool reports public evidence,
not eligibility or a promise that a badge will be awarded.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API = "https://api.github.com"
LOGIN_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")


@dataclass(frozen=True)
class Snapshot:
    login: str
    authored_merged_pr_search_total: int
    owned_public_repo_count: int
    top_owned_repo: str | None
    top_owned_repo_stars: int


def get_json(path: str, token: str | None = None, opener=urlopen) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-achievement-audit/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(API + path, headers=headers)
    with opener(request, timeout=20) as response:
        return json.load(response)


def fetch_snapshot(login: str, token: str | None = None, opener=urlopen) -> Snapshot:
    if not LOGIN_RE.fullmatch(login):
        raise ValueError("Login must be a valid GitHub username")

    # The public repos endpoint is paginated. Forks are excluded from the
    # Starstruck candidate list; we do not infer GitHub's private badge rules.
    owned_repos: list[dict] = []
    page = 1
    while True:
        query = urlencode({"per_page": 100, "page": page, "type": "owner"})
        batch = get_json(f"/users/{quote(login)}/repos?{query}", token, opener)
        if not isinstance(batch, list):
            raise ValueError("Unexpected repositories response from GitHub API")
        owned_repos.extend(repo for repo in batch if isinstance(repo, dict) and not repo.get("fork"))
        if len(batch) < 100:
            break
        page += 1
        if page > 100:
            raise ValueError("Repository pagination exceeded 100 pages")

    pr_query = urlencode({"q": f"is:pr is:merged author:{login}", "per_page": 1})
    search = get_json(f"/search/issues?{pr_query}", token, opener)
    if not isinstance(search, dict) or not isinstance(search.get("total_count"), int):
        raise ValueError("Unexpected pull request search response from GitHub API")

    top = max(owned_repos, key=lambda repo: int(repo.get("stargazers_count") or 0), default=None)
    return Snapshot(
        login=login,
        authored_merged_pr_search_total=search["total_count"],
        owned_public_repo_count=len(owned_repos),
        top_owned_repo=top.get("full_name") if top else None,
        top_owned_repo_stars=int(top.get("stargazers_count") or 0) if top else 0,
    )


def render_markdown(snapshot: Snapshot) -> str:
    login = snapshot.login
    pr_search = "https://github.com/pulls?q=" + quote(f"is:pr is:merged author:{login}")
    repo_label = (
        f"[{snapshot.top_owned_repo}](https://github.com/{snapshot.top_owned_repo})"
        if snapshot.top_owned_repo
        else "none"
    )
    return "\n".join(
        [
            f"# Public GitHub signals for [{login}](https://github.com/{login})",
            "",
            "> Read-only snapshot. GitHub does not publish an Achievement counter API; these numbers are not badge eligibility counts.",
            "",
            "| Signal | Public result |",
            "| --- | ---: |",
            f"| [Authored merged PR search]({pr_search}) | {snapshot.authored_merged_pr_search_total} |",
            f"| Non-fork public repositories | {snapshot.owned_public_repo_count} |",
            f"| Most-starred non-fork repository: {repo_label} | {snapshot.top_owned_repo_stars} stars |",
            "",
            "PR search may include events GitHub does not count for Pull Shark. A repository's stars do not guarantee Starstruck. Check the badges on the profile itself.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("login", help="GitHub username")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable snapshot")
    args = parser.parse_args(argv)
    try:
        snapshot = fetch_snapshot(args.login, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    except (HTTPError, URLError, ValueError) as exc:
        print(f"GitHub audit failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(snapshot.__dict__, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
