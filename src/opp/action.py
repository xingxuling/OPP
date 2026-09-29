"""Bounded Agent Action Contract profile for OPP.

OPP describes what an action may do. It never grants authority. The resulting
contract is intended to be consumed by TINP or another enforcement plane.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .capability import _payload
from .integrity import content_root

ACTION_FORMAT = "taowind.opp.agent-action-contract.v0.1"
KNOWN_EFFECTS = frozenset({
    "filesystem.read", "filesystem.write", "credential.read", "credential.write",
    "network.egress", "process.spawn", "package.install", "package.script",
    "registry.publish", "git.write",
})
_EFFECT_ALIASES = {
    "workspace.read": "filesystem.read",
    "workspace.write": "filesystem.write",
    "file.read": "filesystem.read",
    "file.write": "filesystem.write",
    "secret.read": "credential.read",
    "secrets.read": "credential.read",
    "shell.spawn": "process.spawn",
    "command.spawn": "process.spawn",
    "npm.install": "package.install",
    "npm.postinstall": "package.script",
    "package.postinstall": "package.script",
    "network.write": "network.egress",
    "http.write": "network.egress",
    "github.write": "git.write",
}
_RESOURCE_KEYS = frozenset({"filesystem", "network", "commands", "packages"})
_EFFECT_RESOURCE = {
    "filesystem.read": "filesystem",
    "filesystem.write": "filesystem",
    "credential.read": "filesystem",
    "credential.write": "filesystem",
    "network.egress": "network",
    "process.spawn": "commands",
    "package.install": "packages",
    "package.script": "packages",
    "registry.publish": "network",
    "git.write": "network",
}


class ActionContractError(ValueError):
    """Stable fail-closed error for Agent Action Contract validation."""


def _canon_effect(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ActionContractError("ACTION_EFFECT_INVALID")
    raw = value.strip().lower()
    return _EFFECT_ALIASES.get(raw, raw)


def _effects(values: Iterable[str]) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise ActionContractError("ACTION_EFFECTS_ARRAY_REQUIRED")
    return sorted({_canon_effect(v) for v in values})


def _resources(value: Mapping[str, Any] | None) -> dict[str, list[str]]:
    value = {} if value is None else value
    if not isinstance(value, Mapping) or set(value) - _RESOURCE_KEYS:
        raise ActionContractError("ACTION_RESOURCES_INVALID")
    out: dict[str, list[str]] = {}
    for key in sorted(_RESOURCE_KEYS):
        items = value.get(key, [])
        if isinstance(items, (str, bytes)) or not isinstance(items, (list, tuple)):
            raise ActionContractError(f"ACTION_RESOURCE_LIST_REQUIRED:{key}")
        normalized = []
        for item in items:
            if not isinstance(item, str) or not item.strip() or len(item) > 4096:
                raise ActionContractError(f"ACTION_RESOURCE_INVALID:{key}")
            normalized.append(item.strip())
        out[key] = sorted(set(normalized))
    return out


def _required_resource_reasons(effects: list[str], resources: Mapping[str, list[str]]) -> list[str]:
    reasons = []
    for effect in effects:
        key = _EFFECT_RESOURCE.get(effect)
        if key and not resources.get(key):
            reasons.append(f"RESOURCE_BINDING_REQUIRED:{effect}")
    return reasons


def build_action_contract(
    capability: Mapping[str, Any], *,
    action_id: str,
    accepted_effects: Iterable[str] = (),
    resources: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a fail-closed action contract from an RCP declaration.

    The caller must acknowledge the provider's complete declared effect set.
    Unknown effects force negotiation rather than being silently downgraded.
    Authority is copied as a requirement only; OPP never grants it.
    """
    if not isinstance(action_id, str) or not action_id.strip() or len(action_id) > 256:
        raise ActionContractError("ACTION_ID_INVALID")

    payload = _payload(capability, "provider")
    declared = _effects(payload.get("sideEffects", ()))
    accepted = _effects(accepted_effects)
    bound = _resources(resources)
    reasons: list[str] = []

    unknown = sorted(set(declared) - KNOWN_EFFECTS)
    if unknown:
        reasons.extend(f"UNKNOWN_EFFECT:{effect}" for effect in unknown)
    if declared != accepted:
        reasons.append("EFFECT_ACKNOWLEDGEMENT_MISMATCH")
    reasons.extend(_required_resource_reasons(declared, bound))

    reversibility = payload.get("reversibility", "unknown")
    if declared and reversibility == "unknown":
        reasons.append("REVERSIBILITY_EXPLICITNESS_REQUIRED")

    body = {
        "format": ACTION_FORMAT,
        "actionId": action_id.strip(),
        "capabilityId": str(payload.get("capabilityId", "")),
        "capabilityRoot": content_root(capability),
        "operation": str(payload.get("operation", "")),
        "requiredAuthority": sorted(set(payload.get("authorityRequired", ()))),
        "declaredEffects": declared,
        "acceptedEffects": accepted,
        "resources": bound,
        "reversibility": reversibility,
        "status": "accepted" if not reasons else "negotiate",
        "reasons": reasons,
        "authorityGranted": False,
        "requiresTINP": True,
        "boundary": (
            "OPP describes a bounded action and its potential effects. It does not "
            "authenticate identity, grant authority, prove runtime isolation, or attest "
            "that execution matched the declaration."
        ),
    }
    return {**body, "contractRoot": content_root(body)}


def verify_action_contract(
    contract: Mapping[str, Any], *,
    capability: Mapping[str, Any] | None = None,
    expected_root: str | None = None,
) -> bool:
    """Verify roots, effect acknowledgement and capability binding."""
    if not isinstance(contract, Mapping):
        raise ActionContractError("ACTION_CONTRACT_OBJECT_REQUIRED")
    root = contract.get("contractRoot")
    body = {k: deepcopy(v) for k, v in contract.items() if k != "contractRoot"}
    if body.get("format") != ACTION_FORMAT or root != content_root(body):
        raise ActionContractError("ACTION_CONTRACT_ROOT_INVALID")
    if expected_root is not None and root != expected_root:
        raise ActionContractError("ACTION_CONTRACT_EXPECTED_ROOT_MISMATCH")
    if body.get("authorityGranted") is not False or body.get("requiresTINP") is not True:
        raise ActionContractError("ACTION_CONTRACT_AUTHORITY_BOUNDARY_INVALID")
    if body.get("status") != "accepted" or body.get("reasons"):
        raise ActionContractError("ACTION_CONTRACT_NOT_ACCEPTED")

    declared = _effects(body.get("declaredEffects", ()))
    accepted = _effects(body.get("acceptedEffects", ()))
    if declared != accepted:
        raise ActionContractError("ACTION_CONTRACT_EFFECT_DRIFT")
    resources = _resources(body.get("resources"))
    if _required_resource_reasons(declared, resources):
        raise ActionContractError("ACTION_CONTRACT_RESOURCE_BINDING_MISSING")

    if capability is not None:
        payload = _payload(capability, "provider")
        if body.get("capabilityRoot") != content_root(capability):
            raise ActionContractError("ACTION_CONTRACT_CAPABILITY_ROOT_MISMATCH")
        if body.get("capabilityId") != payload.get("capabilityId"):
            raise ActionContractError("ACTION_CONTRACT_CAPABILITY_ID_MISMATCH")
        if body.get("requiredAuthority") != sorted(set(payload.get("authorityRequired", ()))):
            raise ActionContractError("ACTION_CONTRACT_AUTHORITY_DRIFT")
        if declared != _effects(payload.get("sideEffects", ())):
            raise ActionContractError("ACTION_CONTRACT_DECLARATION_DRIFT")
    return True


__all__ = [
    "ACTION_FORMAT", "KNOWN_EFFECTS", "ActionContractError",
    "build_action_contract", "verify_action_contract",
]
