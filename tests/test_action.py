from copy import deepcopy

import pytest

from opp.action import ActionContractError, build_action_contract, verify_action_contract
from opp.integrity import seal_envelope


def capability(*, effects, authority=("workspace.read",), reversibility="reversible"):
    return seal_envelope({
        "format": "taowind.opp.reality-envelope.v0.1",
        "protocol": "opp.rcp.v0.1",
        "version": "0.1.0-candidate.1",
        "kind": "capability",
        "id": "capability:agent-tool",
        "status": "candidate",
        "issuedAt": "2026-09-29T00:00:00Z",
        "issuer": {"id": "tool", "type": "runtime", "displayName": "tool"},
        "payload": {
            "capabilityId": "agent.tool",
            "name": "Agent tool",
            "domain": "agent.action",
            "operation": "run",
            "inputModalities": ["json"],
            "outputModalities": ["json"],
            "inputSchema": None,
            "outputSchema": None,
            "determinism": "unknown",
            "statefulness": "session",
            "streaming": False,
            "authorityRequired": list(authority),
            "sideEffects": list(effects),
            "reversibility": reversibility,
            "availability": "candidate-only",
            "costProfile": {},
            "latencyProfile": {},
            "rights": {},
            "evidence": ["test:agent-action"],
            "claimBoundary": "Test fixture only.",
        },
        "constraints": [],
        "evidenceRefs": [],
        "extensions": {},
    })


def test_read_scope_becomes_a_resource_bound_security_effect():
    declared = capability(effects=[])
    rejected = build_action_contract(declared, action_id="action:read")
    assert rejected["status"] == "negotiate"
    assert "RESOURCE_BINDING_REQUIRED:filesystem.read" in rejected["reasons"]

    contract = build_action_contract(
        declared,
        action_id="action:read",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/file.txt"]},
    )
    assert contract["status"] == "accepted"
    assert contract["declaredEffects"] == ["filesystem.read"]
    assert contract["authorityGranted"] is False
    assert contract["requiresTINP"] is True
    assert verify_action_contract(contract, capability=declared)


def test_workspace_write_requires_exact_ack_and_resource_binding():
    declared = capability(
        effects=["workspace.write"],
        authority=("workspace.write",),
        reversibility="compensatable",
    )
    rejected = build_action_contract(declared, action_id="action:write", accepted_effects=[])
    assert rejected["status"] == "negotiate"
    assert "EFFECT_ACKNOWLEDGEMENT_MISMATCH" in rejected["reasons"]

    accepted = build_action_contract(
        declared,
        action_id="action:write",
        accepted_effects=["filesystem.write"],
        resources={"filesystem": ["workspace/project"]},
    )
    assert accepted["status"] == "accepted"
    assert accepted["declaredEffects"] == ["filesystem.write"]
    assert verify_action_contract(accepted, capability=declared)


def test_sensitive_effect_without_bound_resource_fails_closed():
    declared = capability(
        effects=["credential.read"],
        authority=("credential.read",),
        reversibility="irreversible",
    )
    contract = build_action_contract(
        declared,
        action_id="action:credential",
        accepted_effects=["credential.read"],
    )
    assert contract["status"] == "negotiate"
    assert "RESOURCE_BINDING_REQUIRED:credential.read" in contract["reasons"]


def test_unknown_effect_forces_negotiation():
    declared = capability(
        effects=["mystery.kernel.patch"],
        authority=("admin",),
        reversibility="irreversible",
    )
    contract = build_action_contract(
        declared,
        action_id="action:unknown",
        accepted_effects=["mystery.kernel.patch"],
    )
    assert contract["status"] == "negotiate"
    assert any(reason.startswith("UNKNOWN_EFFECT:") for reason in contract["reasons"])


def test_tamper_is_detected():
    declared = capability(effects=[])
    contract = build_action_contract(declared, action_id="action:read")
    tampered = deepcopy(contract)
    tampered["actionId"] = "action:tampered"
    with pytest.raises(ActionContractError, match="ROOT_INVALID"):
        verify_action_contract(tampered)
