# GitHub Achievement Audit

A small, **read-only** GitHub API tool for tracking public signals relevant to profile Achievements. It lists your authored merged PR search total and your most-starred non-fork public repository. It never creates PRs, stars, comments, or follows.

GitHub does not publish an Achievement counter API. Search totals are **not** Pull Shark counts, and repo stars do **not** guarantee Starstruck. The only definitive status is on your GitHub profile.

## Run

Python 3.10+ and the standard library are enough:

```bash
python3 audit.py jackiectl2
python3 audit.py jackiectl2 --json
```

An optional `GH_TOKEN` or `GITHUB_TOKEN` increases API rate limits. The token is sent only in the `Authorization` header to `api.github.com`; the tool never prints or stores it. A token with read-only access is sufficient. Without a token, public API rate limits apply.

## Tests

```bash
python3 -m unittest -v test_audit.py
```

The test uses a fake HTTP response and makes no network requests.

## API calls

- [`GET /users/{username}/repos`](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user), paginated, filtered locally to non-forks.
- [`GET /search/issues`](https://docs.github.com/en/rest/search/search#search-issues-and-pull-requests) with `is:pr is:merged author:LOGIN`.

GitHub's [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) prohibit inauthentic engagement and automated bulk activity. This tool is deliberately read-only and makes only the few requests needed for a snapshot.

## Support

Open a GitHub issue in this repository for bugs or suggestions. For private support, use the contact address shown on [the maintainer's public profile](https://github.com/jackiectl2).
