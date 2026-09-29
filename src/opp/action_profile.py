"""Bounded Agent Action Profile for OPP.

OPP owns semantic compatibility, not authority. This module turns an agent's
proposed action and a provider's declared action surface into a reproducible,
rooted compatibility contract. Whether a caller is actually allowed to use the
contract is intentionally left to an authority plane such as TINP.
"""
from __future__ import annotations
from copy import deepcopy
from .integrity import content_root

ACTION_PROFILE = "opp.agent-action.v0.1"
OUTCOMES = ("DIRECT", "NEGOTIATE", "REJECT")
_ALLOWED_EFFECTS = {"none","read","write","execute","network","install","delete"}
_ALLOWED_REVERSIBILITY = {"none","reversible","compensatable","irreversible","unknown"}

class ActionProfileError(ValueError):
    pass

def _sealed(body: dict, key: str) -> dict:
    value = deepcopy(body)
    value[key] = content_root(value)
    return value

def _nonempty_text(value, field, *, max_len=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ActionProfileError(f"INVALID_{field.upper()}")
    return value.strip()

def _strings(value, field, *, max_items=128, max_len=512):
    if not isinstance(value, (list, tuple)) or len(value) > max_items:
        raise ActionProfileError(f"INVALID_{field.upper()}")
    result = []
    for item in value:
        item = _nonempty_text(item, field, max_len=max_len)
        if item not in result:
            result.append(item)
    return sorted(result)

def _resource_matches(resource: str, scopes: list[str]) -> bool:
    for scope in scopes:
        if scope.endswith("*") and resource.startswith(scope[:-1]):
            return True
        if resource == scope:
            return True
    return False

def _host_matches(host: str, patterns: list[str]) -> bool:
    host = host.lower().rstrip(".")
    for pattern in patterns:
        p = pattern.lower().rstrip(".")
        if p.startswith("*.") and host.endswith(p[1:]) and host != p[2:]:
            return True
        if host == p:
            return True
    return False

def normalize_action_request(request: dict) -> dict:
    if not isinstance(request, dict):
        raise ActionProfileError("INVALID_REQUEST")
    profile = request.get("profile", ACTION_PROFILE)
    if profile != ACTION_PROFILE:
        raise ActionProfileError("ACTION_PROFILE_UNSUPPORTED")
    action = _nonempty_text(request.get("action"), "action", max_len=256)
    resource = _nonempty_text(request.get("resource"), "resource")
    effect = request.get("sideEffect", "none")
    if effect not in _ALLOWED_EFFECTS:
        raise ActionProfileError("INVALID_SIDE_EFFECT")
    reversibility = request.get("reversibility", "unknown")
    if reversibility not in _ALLOWED_REVERSIBILITY:
        raise ActionProfileError("INVALID_REVERSIBILITY")
    network_host = request.get("networkHost")
    if network_host is not None:
        network_host = _nonempty_text(network_host, "networkHost", max_len=253).lower()
    return _sealed({
        "format":"taowind.opp.agent-action-request.v0.1","profile":ACTION_PROFILE,
        "action":action,"resource":resource,"sideEffect":effect,"reversibility":reversibility,
        "dataClasses":_strings(request.get("dataClasses", []), "dataClasses"),
        "networkHost":network_host,
        "origin":_nonempty_text(request.get("origin", "agent"), "origin", max_len=256),
        "authorityGranted":False,
    }, "requestRoot")

def normalize_action_provider(provider: dict) -> dict:
    if not isinstance(provider, dict):
        raise ActionProfileError("INVALID_PROVIDER")
    if provider.get("profile", ACTION_PROFILE) != ACTION_PROFILE:
        raise ActionProfileError("ACTION_PROFILE_UNSUPPORTED")
    effects = _strings(provider.get("sideEffects", []), "sideEffects", max_items=32, max_len=64)
    if any(x not in _ALLOWED_EFFECTS for x in effects):
        raise ActionProfileError("INVALID_PROVIDER_SIDE_EFFECT")
    reversibility = _strings(provider.get("reversibility", []), "reversibility", max_items=16, max_len=64)
    if any(x not in _ALLOWED_REVERSIBILITY for x in reversibility):
        raise ActionProfileError("INVALID_PROVIDER_REVERSIBILITY")
    return _sealed({
        "format":"taowind.opp.agent-action-provider.v0.1","profile":ACTION_PROFILE,
        "providerId":_nonempty_text(provider.get("providerId"), "providerId", max_len=256),
        "actions":_strings(provider.get("actions", []), "actions", max_items=256, max_len=256),
        "resourceScopes":_strings(provider.get("resourceScopes", []), "resourceScopes"),
        "networkHosts":_strings(provider.get("networkHosts", []), "networkHosts", max_items=256, max_len=253),
        "sideEffects":effects,"reversibility":reversibility,
        "authorityRequired":_strings(provider.get("authorityRequired", []), "authorityRequired", max_items=128, max_len=256),
        "claimBoundary":"Capability declaration only; no identity, trust, permission or execution authority is created.",
        "authorityGranted":False,
    }, "providerRoot")

def negotiate_agent_action(request: dict, provider: dict) -> dict:
    """Build a semantic compatibility contract; never grant authority."""
    req = normalize_action_request(request)
    pro = normalize_action_provider(provider)
    reasons, outcome = [], "DIRECT"
    if req["action"] not in pro["actions"]:
        outcome, reasons = "REJECT", ["ACTION_UNSUPPORTED"]
    elif not _resource_matches(req["resource"], pro["resourceScopes"]):
        outcome, reasons = "REJECT", ["RESOURCE_SCOPE_UNSUPPORTED"]
    elif req["sideEffect"] not in pro["sideEffects"]:
        outcome, reasons = "REJECT", ["SIDE_EFFECT_UNSUPPORTED"]
    elif req["reversibility"] not in pro["reversibility"]:
        outcome, reasons = "NEGOTIATE", ["REVERSIBILITY_NOT_DECLARED"]
    elif req["action"] == "network.egress":
        host = req.get("networkHost")
        if not host:
            outcome, reasons = "NEGOTIATE", ["NETWORK_HOST_REQUIRED"]
        elif not _host_matches(host, pro["networkHosts"]):
            outcome, reasons = "REJECT", ["NETWORK_HOST_UNSUPPORTED"]
    contract = None
    if outcome == "DIRECT":
        contract = _sealed({
            "format":"taowind.opp.agent-action-contract.v0.1","profile":ACTION_PROFILE,
            "requestRoot":req["requestRoot"],"providerRoot":pro["providerRoot"],
            "action":req["action"],"resource":req["resource"],"networkHost":req.get("networkHost"),
            "sideEffect":req["sideEffect"],"reversibility":req["reversibility"],
            "requiredAuthority":pro["authorityRequired"],"authorityGranted":False,
            "boundary":"Semantic compatibility only. TINP/host authority must independently authorize each execution.",
        }, "contractRoot")
    return _sealed({
        "format":"taowind.opp.agent-action-negotiation.v0.1","profile":ACTION_PROFILE,
        "outcome":outcome,"reasons":reasons or ["DECLARATIONS_COMPATIBLE"],
        "request":req,"provider":pro,"contract":contract,"authorityGranted":False,
    }, "negotiationRoot")

def verify_agent_action_contract(negotiation: dict) -> bool:
    if not isinstance(negotiation, dict):
        raise ActionProfileError("NEGOTIATION_INVALID")
    root = negotiation.get("negotiationRoot")
    if root != content_root({k:v for k,v in negotiation.items() if k != "negotiationRoot"}):
        raise ActionProfileError("NEGOTIATION_ROOT_MISMATCH")
    regenerated = negotiate_agent_action(negotiation["request"], negotiation["provider"])
    if negotiation.get("outcome") != regenerated.get("outcome"):
        raise ActionProfileError("NEGOTIATION_NOT_REPRODUCIBLE")
    if negotiation.get("contract") != regenerated.get("contract"):
        raise ActionProfileError("CONTRACT_NOT_REPRODUCIBLE")
    if negotiation.get("authorityGranted") is not False:
        raise ActionProfileError("AUTHORITY_MUST_REMAIN_FALSE")
    return True
