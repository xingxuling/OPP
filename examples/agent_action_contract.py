"""Emit one bounded OPP Action Contract for the TINP gateway demo."""
import json

from opp.action_contract import build_action_contract

capability = {
    "format": "taowind.opp.reality-envelope.v0.1",
    "protocol": "opp.rcp.v0.1",
    "version": "0.1.0-candidate.1",
    "kind": "capability",
    "id": "cap:code",
    "status": "candidate",
    "issuedAt": "2026-09-29T00:00:00Z",
    "issuer": {"id": "agent:coder", "type": "agent"},
    "payload": {
        "capabilityId": "code.edit",
        "name": "Code edit",
        "domain": "software",
        "operation": "edit",
        "inputModalities": ["json"],
        "outputModalities": ["json"],
        "determinism": "unknown",
        "statefulness": "session",
        "authorityRequired": ["workspace.edit"],
        "sideEffects": ["filesystem.write"],
        "reversibility": "compensatable",
        "availability": "candidate-only",
        "evidence": [],
    },
}

contract = build_action_contract(
    capability,
    subject_id="agent:coder",
    requested_effects=[
        {
            "kind": "filesystem.write",
            "resource": "workspace:/project/src/app.js",
        }
    ],
    action_input={"prompt": "patch app.js"},
)

print(json.dumps(contract, ensure_ascii=False, sort_keys=True, indent=2))
