"""Read-only GitHub REST producer used by a manual OPP third-party audit.

This fixture is intentionally not part of the default test suite. It performs
one explicit GET only when an operator supplies an invocation consent gate.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch_repository(repo: str, timeout_seconds: int = 15) -> dict:
    if not isinstance(repo, str) or not repo or "/" not in repo:
        raise ValueError("REPOSITORY_SLUG_REQUIRED")
    request = Request(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "taowind-opp-third-party-audit",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"GITHUB_HTTP_STATUS:{response.status}")
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"GITHUB_HTTP_STATUS:{exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"GITHUB_NETWORK_ERROR:{type(exc.reason).__name__}") from exc
    return {
        "full_name": payload["full_name"],
        "default_branch": payload["default_branch"],
        "private": payload["private"],
    }
