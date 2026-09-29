from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

PROFILE = "opp.agent-action.v0.1"

_OPERATION_MAP: Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "filesystem.read": (("workspace.read",), ("filesystem.read",)),
    "filesystem.write": (("workspace.write",), ("filesystem.write",)),
    "shell.exec": (("process.spawn",), ("process.spawn",)),
    "network.egress": (("network.egress",), ("network.egress",)),
    "credential.read": (("credential.read",), ("credential.read",)),
    "package.install": (("package.install", "workspace.write", "network.egress"),
                        ("package.install", "filesystem.write", "network.egress")),
    "package.lifecycle-script": (("process.spawn",), ("process.spawn",)),
    "scm.write": (("scm.write", "network.egress"), ("scm.write", "network.egress")),
}

_ALLOWED_REVERSIBILITY = {"reversible", "partial", "irreversible", "unknown"}


class AgentActionContractError(ValueError):
    """Raised when an action cannot be represented without guessing."""


def _root(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def _clean_strings(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise AgentActionContractError(f"{field} must contain non-empty strings")
        item = value.strip()
        if len(item) > 512:
            raise AgentActionContractError(f"{field} item too long")
        if item not in out:
            out.append(item)
    return tuple(sorted(out))


@dataclass(frozen=True)
class AgentActionContract:
    profile: str
    action_id: str
    operations: tuple[str, ...]
    authorities: tuple[str, ...]
    side_effects: tuple[str, ...]
    targets: tuple[str, ...]
    network_destinations: tuple[str, ...]
    reversibility: str
    human_approval_required: bool
    contract_root: str

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "actionId": self.action_id,
            "operations": list(self.operations),
            "authorities": list(self.authorities),
            "sideEffects": list(self.side_effects),
            "targets": list(self.targets),
            "networkDestinations": list(self.network_destinations),
            "reversibility": self.reversibility,
            "humanApprovalRequired": self.human_approval_required,
            "contractRoot": self.contract_root,
            "authorityGranted": False,
            "executable": False,
        }


def compile_agent_action_contract(
    *,
    action_id: str,
    operations: Sequence[str],
    targets: Sequence[str] = (),
    network_destinations: Sequence[str] = (),
    reversibility: str = "unknown",
    human_approval_required: bool = False,
) -> AgentActionContract:
    """Compile an explicit Code-Agent/MCP action into a deterministic OPP profile.

    Unknown operations fail closed. The result is descriptive only: it does not
    authorize or execute anything. TINP (or another control plane) must evaluate
    the authority vector against an authenticated lease/policy.
    """
    if not isinstance(action_id, str) or not action_id.strip() or len(action_id) > 256:
        raise AgentActionContractError("action_id must be a non-empty string <= 256 chars")
    ops = _clean_strings(operations, field="operations")
    if not ops:
        raise AgentActionContractError("at least one operation is required")
    unknown = [op for op in ops if op not in _OPERATION_MAP]
    if unknown:
        raise AgentActionContractError(f"unknown operation(s): {', '.join(unknown)}")
    if reversibility not in _ALLOWED_REVERSIBILITY:
        raise AgentActionContractError(f"unsupported reversibility: {reversibility}")

    authorities: set[str] = set()
    side_effects: set[str] = set()
    for op in ops:
        auth, effects = _OPERATION_MAP[op]
        authorities.update(auth)
        side_effects.update(effects)

    clean_targets = _clean_strings(targets, field="targets")
    clean_network = _clean_strings(network_destinations, field="network_destinations")
    unsigned = {
        "profile": PROFILE,
        "actionId": action_id.strip(),
        "operations": list(ops),
        "authorities": sorted(authorities),
        "sideEffects": sorted(side_effects),
        "targets": list(clean_targets),
        "networkDestinations": list(clean_network),
        "reversibility": reversibility,
        "humanApprovalRequired": bool(human_approval_required),
    }
    return AgentActionContract(
        profile=PROFILE,
        action_id=action_id.strip(),
        operations=ops,
        authorities=tuple(unsigned["authorities"]),
        side_effects=tuple(unsigned["sideEffects"]),
        targets=clean_targets,
        network_destinations=clean_network,
        reversibility=reversibility,
        human_approval_required=bool(human_approval_required),
        contract_root=_root(unsigned),
    )


def verify_agent_action_contract(document: Mapping[str, object]) -> bool:
    """Offline structural/root check for an OPP agent-action contract."""
    if not isinstance(document, Mapping) or document.get("profile") != PROFILE:
        return False
    root = document.get("contractRoot")
    if not isinstance(root, str) or len(root) != 64:
        return False
    unsigned = {
        "profile": document.get("profile"),
        "actionId": document.get("actionId"),
        "operations": document.get("operations"),
        "authorities": document.get("authorities"),
        "sideEffects": document.get("sideEffects"),
        "targets": document.get("targets"),
        "networkDestinations": document.get("networkDestinations"),
        "reversibility": document.get("reversibility"),
        "humanApprovalRequired": document.get("humanApprovalRequired"),
    }
    return _root(unsigned) == root


__all__ = [
    "PROFILE",
    "AgentActionContract",
    "AgentActionContractError",
    "compile_agent_action_contract",
    "verify_agent_action_contract",
]
