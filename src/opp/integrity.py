"""Integrity（完整性）工具：提供规范化 JSON 与 SHA-256 内容根。"""
from __future__ import annotations
import copy, hashlib, json, math, struct
from typing import Any, Mapping


LEGACY_CANONICAL_PROFILE = "opp.json-python.v1"
BINARY64_CANONICAL_PROFILE = "opp.json-binary64.v1"
SAFE_INTEGER = 9007199254740991


def native_receipt_format(kind: str, profile: str) -> str:
    if profile not in (LEGACY_CANONICAL_PROFILE, BINARY64_CANONICAL_PROFILE):
        raise ValueError("CANONICAL_PROFILE_UNSUPPORTED")
    return f"taowind.opp.{kind}-receipt.v0.{'1' if profile == LEGACY_CANONICAL_PROFILE else '2'}"


def _binary64_data(value: Any) -> list:
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["boolean", value]
    if isinstance(value, (int, float)):
        if (isinstance(value, int) and abs(value) > SAFE_INTEGER) or not math.isfinite(value) or (value == int(value) and abs(value) > SAFE_INTEGER):
            raise ValueError("CANONICAL_NUMBER_INVALID")
        return ["number", struct.pack(">d", 0.0 if value == 0 else float(value)).hex()]
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError("CANONICAL_STRING_INVALID")
        return ["string", value]
    if isinstance(value, list):
        return ["array", [_binary64_data(item) for item in value]]
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("CANONICAL_OBJECT_KEY_INVALID")
            _binary64_data(key)
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return ["object", [[key, _binary64_data(value[key])] for key in keys]]
    raise ValueError("CANONICAL_DATA_INVALID")


def canonical_json_bytes(value: Any, *, profile: str = LEGACY_CANONICAL_PROFILE) -> bytes:
    """生成 deterministic canonical JSON（确定性规范 JSON）字节。"""
    if profile == LEGACY_CANONICAL_PROFILE:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    native_receipt_format("interop", profile)
    return json.dumps({"profile": profile, "value": _binary64_data(value)},
                      ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def content_root(value: Any, *, profile: str = LEGACY_CANONICAL_PROFILE) -> str:
    """计算 SHA-256 content root（内容根）。"""
    return hashlib.sha256(canonical_json_bytes(value, profile=profile)).hexdigest()


def unsigned_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """移除 integrity（完整性字段），得到被哈希的规范内容。"""
    value = copy.deepcopy(dict(envelope))
    value.pop("integrity", None)
    return value


def seal_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """附加 SHA-256 内容根；这不是数字签名或身份认证。"""
    value = unsigned_envelope(envelope)
    value["integrity"] = {"algorithm": "sha256", "contentRoot": content_root(value)}
    return value


def verify_envelope_root(envelope: Mapping[str, Any]) -> bool:
    integrity = envelope.get("integrity")
    if not integrity:
        return True
    if integrity.get("algorithm") != "sha256":
        return False
    return integrity.get("contentRoot") == content_root(unsigned_envelope(envelope))
