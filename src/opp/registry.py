"""Registry（协议注册表）读取与协议发现。"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_registry() -> dict:
    return json.loads((repository_root() / "registry" / "protocols.json").read_text(encoding="utf-8"))


def protocol_entry(protocol_id: str) -> dict | None:
    for entry in load_registry()["protocols"]:
        if entry["id"] == protocol_id:
            return entry
    return None


def schema_path(relative: str) -> Path:
    return repository_root() / relative
