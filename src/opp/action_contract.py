"""Bounded OPP action-contract projection for Agent security gateways.

This profile does not grant authority. It turns one validated RCP declaration plus
one concrete requested action into a deterministic, rooted contract that an
external authority plane such as TINP can admit or reject.
"""
from __future__ import annotations
from copy import deepcopy
import re
from typing import Any, Mapping, Sequence

from .capability import _payload
from .integrity import content_root

ACTION_CONTRACT_FORMAT = "taowind.opp.action-contract.v0.1"
ACTION_CONTRACT_VERSION = "0.1.0-candidate.1"
BOUNDED_EFFECT_KINDS = frozenset({
    "filesystem.write", "network.egress", "credential.read", "process.spawn",
})
_HIGH_RISK = frozenset({"credential.read", "process.spawn"})
_HASH = re.compile(r"^[0-9a-f]{64}$")


class ActionContractError(ValueError):
    pass


def _effect(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ActionContractError("ACTION_EFFECT_OBJECT_REQUIRED")
    if set(value) != {"kind", "resource"}:
        raise ActionContractError("ACTION_EFFECT_SHAPE_INVALID")
    kind, resource = value.get("kind"), value.get("resource")
    if kind not in BOUNDED_EFFECT_KINDS:
        raise ActionContractError("ACTION_EFFECT_KIND_UNSUPPORTED")
    if not isinstance(resource, str) or not resource.strip() or len(resource) > 4096:
        raise ActionContractError("ACTION_EFFECT_RESOURCE_INVALID")
    return {"kind": kind, "resource": resource}


def _risk(payload: Mapping[str, Any], effects: Sequence[Mapping[str, str]]) -> str:
    kinds = {x["kind"] for x in effects}
    if kinds & _HIGH_RISK or payload.get("reversibility") == "irreversible":
        return "high"
    return "medium" if kinds else "low"


def _normalized_effects(values: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    effects = [_effect(x) for x in values]
    pairs = [(x["kind"], x["resource"]) for x in effects]
    if len(set(pairs)) != len(pairs):
        raise ActionContractError("DUPLICATE_ACTION_EFFECT")
    return sorted(effects, key=lambda x: (x["kind"], x["resource"]))


def build_action_contract(
    capability: Mapping[str, Any],
    *,
    subject_id: str,
    requested_effects: Sequence[Mapping[str, Any]] = (),
    action_input: Any = None,
) -> dict[str, Any]:
    payload = _payload(capability, "capability")
    if not isinstance(subject_id, str) or not subject_id.strip() or len(subject_id) > 1024:
        raise ActionContractError("SUBJECT_ID_INVALID")

    declared = set(payload.get("sideEffects", ()))
    effects = _normalized_effects(requested_effects)
    if any(x["kind"] not in declared for x in effects):
        raise ActionContractError("UNDECLARED_SIDE_EFFECT")

    body = {
        "format": ACTION_CONTRACT_FORMAT,
        "version": ACTION_CONTRACT_VERSION,
        "subjectId": subject_id,
        "capability": deepcopy(dict(capability)),
        "capabilityRoot": content_root(capability),
        "capabilityId": payload["capabilityId"],
        "operation": payload["operation"],
        "authorityRequired": sorted(set(payload.get("authorityRequired", ()))),
        "requestedEffects": effects,
        "reversibility": payload["reversibility"],
        "riskClass": _risk(payload, effects),
        "actionInputRoot": content_root(action_input),
        "authorityGranted": False,
        "boundary": (
            "OPP describes the requested action, effects and contract roots only; "
            "it does not authenticate the subject, grant authority, execute the "
            "action or prove runtime isolation."
        ),
    }
    return {**body, "contractRoot": content_root(body)}


def verify_action_contract(
    contract: Mapping[str, Any], *, expected_root: str | None = None
) -> bool:
    if not isinstance(contract, Mapping):
        raise ActionContractError("ACTION_CONTRACT_OBJECT_REQUIRED")
    required = {
        "format", "version", "subjectId", "capability", "capabilityRoot",
        "capabilityId", "operation", "authorityRequired", "requestedEffects",
        "reversibility", "riskClass", "actionInputRoot", "authorityGranted",
        "boundary", "contractRoot",
    }
    if set(contract) != required:
        raise ActionContractError("ACTION_CONTRACT_SHAPE_INVALID")
    if (
        contract["format"] != ACTION_CONTRACT_FORMAT
        or contract["version"] != ACTION_CONTRACT_VERSION
    ):
        raise ActionContractError("ACTION_CONTRACT_VERSION_UNSUPPORTED")
    if (
        not isinstance(contract["subjectId"], str)
        or not contract["subjectId"].strip()
        or len(contract["subjectId"]) > 1024
    ):
        raise ActionContractError("SUBJECT_ID_INVALID")
    if not isinstance(contract["actionInputRoot"], str) or not _HASH.fullmatch(contract["actionInputRoot"]):
        raise ActionContractError("ACTION_INPUT_ROOT_INVALID")

    root = contract["contractRoot"]
    body = {k: deepcopy(v) for k, v in contract.items() if k != "contractRoot"}
    if (
        not isinstance(root, str)
        or not _HASH.fullmatch(root)
        or root != content_root(body)
        or (expected_root is not None and root != expected_root)
    ):
        raise ActionContractError("ACTION_CONTRACT_ROOT_INVALID")

    payload = _payload(contract["capability"], "capability")
    if contract["capabilityRoot"] != content_root(contract["capability"]):
        raise ActionContractError("CAPABILITY_ROOT_INVALID")
    if (
        contract["capabilityId"] != payload["capabilityId"]
        or contract["operation"] != payload["operation"]
    ):
        raise ActionContractError("CAPABILITY_BINDING_INVALID")
    if contract["authorityRequired"] != sorted(set(payload.get("authorityRequired", ()))):
        raise ActionContractError("AUTHORITY_BINDING_INVALID")

    effects = _normalized_effects(contract["requestedEffects"])
    if effects != contract["requestedEffects"]:
        raise ActionContractError("ACTION_EFFECT_ORDER_INVALID")
    if any(x["kind"] not in set(payload.get("sideEffects", ())) for x in effects):
        raise ActionContractError("UNDECLARED_SIDE_EFFECT")
    if contract["reversibility"] != payload["reversibility"]:
        raise ActionContractError("REVERSIBILITY_BINDING_INVALID")
    if contract["riskClass"] != _risk(payload, effects):
        raise ActionContractError("RISK_CLASS_BINDING_INVALID")
    if contract["authorityGranted"] is not False:
        raise ActionContractError("AUTHORITY_PROMOTION_FORBIDDEN")
    return True


__all__ = [
    "ACTION_CONTRACT_FORMAT", "ACTION_CONTRACT_VERSION", "BOUNDED_EFFECT_KINDS",
    "ActionContractError", "build_action_contract", "verify_action_contract",
]
