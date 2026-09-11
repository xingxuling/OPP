"""Local consumer for the manual GitHub REST OPP audit."""
from __future__ import annotations


def accept_repository(full_name: str, default_branch: str, private: bool) -> dict:
    return {
        "accepted": True,
        "full_name": full_name,
        "default_branch": default_branch,
        "private": private,
    }
