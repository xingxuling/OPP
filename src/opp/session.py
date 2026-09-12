"""Opt-in CHA sessions, composed from RCP, SemanticPort and existing JSON bridges.

This bounded profile handles closed objects and explicitly asserted field meanings.
It neither infers business meaning nor implements a transport or authority service.
"""
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from jsonschema import Draft202012Validator

from .bridge.semantic_model import SemanticPort
from .bridge.synthesize import synthesize_bridge
from .bridge.transform import apply_transform
from .capability import _payload
from .integrity import content_root
from .registry import read_json_resource
from .surfaces import SESSION_PROFILE

OUTCOMES = ("DIRECT", "ADAPT", "NEGOTIATE", "DEGRADE", "REJECT")
_SCHEMA_KEYS = {"type", "properties", "required", "additionalProperties", "items",
                "enum", "const", "minimum", "maximum", "exclusiveMinimum",
                "exclusiveMaximum", "multipleOf", "minLength", "maxLength",
                "minItems", "maxItems", "uniqueItems", "title", "description"}


class SessionError(ValueError):
    """A stable failure code; no transport exception text or credentials."""


def _seal(body, key):
    return {**body, key: content_root(body)}


def _check_root(value, key, expected=None):
    root = value.get(key)
    if root != content_root({k: v for k, v in value.items() if k != key}):
        raise SessionError(f"{key.upper()}_MISMATCH")
    if expected is not None and root != expected:
        raise SessionError("EXPECTED_ROOT_MISMATCH")


def _supported_schema(schema):
    if not isinstance(schema, dict) or not schema or set(schema) - _SCHEMA_KEYS:
        return False
    if not isinstance(schema.get("type"), str):
        return False
    try:
        Draft202012Validator.check_schema(schema)
    except Exception:
        return False
    if schema.get("type") == "object":
        return (schema.get("additionalProperties") is False and
                all(_supported_schema(s) for s in schema.get("properties", {}).values()))
    if schema.get("type") == "array":
        return _supported_schema(schema.get("items"))
    return schema.get("type") in {"string", "integer", "number", "boolean", "null"}


def _shape(schema):
    # Descriptions are not semantic equivalence evidence; explicit declarations are.
    result = deepcopy(schema)
    for key in ("title", "description"):
        result.pop(key, None)
    if "properties" in result:
        result["properties"] = {name: _shape(child) for name, child in result["properties"].items()}
    if isinstance(result.get("items"), dict):
        result["items"] = _shape(result["items"])
    return result


def _plan(producer, consumer, goal, available_authority, allowed_drops):
    pp, cp = _payload(producer, "producer"), _payload(consumer, "consumer")
    profiles = [v.get("extensions", {}).get("session", {}) for v in (producer, consumer)]
    if any(not isinstance(p, dict) for p in profiles):
        return "REJECT", ["INVALID_SESSION_PROFILE"], None
    if any(p.get("profile") != SESSION_PROFILE for p in profiles):
        return "REJECT", ["COMMON_SESSION_PROFILE_REQUIRED"], None
    if goal != cp["capabilityId"]:
        return "REJECT", ["GOAL_CAPABILITY_MISMATCH"], None
    required = set(pp["authorityRequired"]) | set(cp["authorityRequired"])
    if required - set(available_authority):
        return "REJECT", ["AUTHORITY_GAP"], None
    for declaration, payload, profile in zip((producer, consumer), (pp, cp), profiles):
        if declaration["status"] in {"rejected", "deprecated"}:
            return "REJECT", ["DECLARATION_NOT_ACTIVE"], None
        if payload["availability"] == "offline":
            return "REJECT", ["PROVIDER_OFFLINE"], None
        if (set(profile) != {"profile", "surface", "semantics"} or
                payload["availability"] == "degraded" or declaration.get("constraints") or payload.get("rights") or
                payload.get("costProfile") or payload.get("latencyProfile") or
                payload.get("streaming") or payload["sideEffects"] or
                payload["statefulness"] != "stateless"):
            return "NEGOTIATE", ["PROVIDER_POLICY_REQUIRES_EXPLICIT_IMPLEMENTATION"], None
        surface = profile.get("surface", {})
        if not isinstance(surface, dict) or any(not isinstance(surface.get(k), str) or not surface[k]
               for k in ("kind", "bindingId", "revision", "discoveryRoot")):
            return "REJECT", ["SURFACE_BINDING_REQUIRED"], None
        meanings = profile.get("semantics")
        if (not isinstance(meanings, dict) or set(meanings) - {"input", "output"} or
                any(not isinstance(side, dict) or any(not isinstance(m, dict) for m in side.values())
                    for side in meanings.values())):
            return "NEGOTIATE", ["SEMANTIC_DECLARATION_INVALID_OR_UNSUPPORTED"], None
        for key in ("inputSchema", "outputSchema"):
            if not _supported_schema(payload.get(key)):
                return "NEGOTIATE", ["SCHEMA_PROOF_UNSUPPORTED"], None
    ps, cs = _shape(pp["outputSchema"]), _shape(cp["inputSchema"])
    if ps.get("type") != "object" or cs.get("type") != "object":
        return "NEGOTIATE", ["OBJECT_SESSION_PROFILE_REQUIRED"], None
    # Only flat field transforms; do not flatten nested rename operations.
    if set(ps) - {"type", "properties", "required", "additionalProperties"} or set(cs) - {
            "type", "properties", "required", "additionalProperties"}:
        return "NEGOTIATE", ["OBJECT_CONSTRAINT_PROOF_UNSUPPORTED"], None
    pfields, cfields = ps.get("properties", {}), cs.get("properties", {})
    pmean = profiles[0].get("semantics", {}).get("output", {})
    cmean = profiles[1].get("semantics", {}).get("input", {})
    mapping, used, operations = {}, set(), []
    for target, target_schema in cfields.items():
        meaning = cmean.get(target, {})
        if (set(meaning) != {"concept", "unit"} or
                not isinstance(meaning.get("concept"), str) or not meaning["concept"] or
                not isinstance(meaning.get("unit"), str) or not meaning["unit"]):
            return "NEGOTIATE", [f"SEMANTIC_EVIDENCE_REQUIRED:{target}"], None
        candidates = [k for k in pfields if pmean.get(k, {}).get("concept") == meaning["concept"]]
        if len(candidates) != 1:
            return "NEGOTIATE", [f"SEMANTIC_MAPPING_AMBIGUOUS_OR_MISSING:{target}"], None
        source = candidates[0]
        if set(pmean[source]) != {"concept", "unit"}:
            return "NEGOTIATE", ["SEMANTIC_QUALIFIERS_UNSUPPORTED"], None
        if pmean[source].get("unit") != meaning["unit"]:
            return "REJECT", [f"UNIT_CONVERSION_NOT_AUTHORIZED:{source}:{target}"], None
        if source in used:
            return "NEGOTIATE", ["NON_BIJECTIVE_MAPPING_UNSUPPORTED"], None
        if source not in ps.get("required", []):
            return "NEGOTIATE", [f"PRODUCER_FIELD_NOT_GUARANTEED:{source}"], None
        if source != target and target in pfields:
            return "NEGOTIATE", ["RENAME_COLLISION_OR_CYCLE"], None
        a, b = pfields[source], target_schema
        widened = {**a, "type": "number"} if a.get("type") == "integer" else a
        if a != b and widened != b:
            outcome = "REJECT" if a.get("type") != b.get("type") else "NEGOTIATE"
            return outcome, [f"TYPE_OR_CONSTRAINT_NOT_PROVEN:{source}:{target}"], None
        mapping[target] = source
        used.add(source)
        if source != target:
            operations.append({"op": "rename", "from": source, "to": target})
    drops = sorted(set(pfields) - used)
    if set(allowed_drops) - set(drops):
        return "REJECT", ["DROP_CONSENT_DOES_NOT_MATCH_PLAN"], None
    if drops and set(drops) != set(allowed_drops):
        return "NEGOTIATE", ["EXPLICIT_DROP_CONSENT_REQUIRED:" + ",".join(drops)], None
    # After semantic renaming, reuse the existing synthesizer for structural proof
    # and any explicitly consented projection. No new transform interpreter.
    mapped = deepcopy(ps)
    mapped["properties"] = {next((t for t, s in mapping.items() if s == k), k): v
                             for k, v in pfields.items()}
    mapped["required"] = [next((t for t, s in mapping.items() if s == k), k)
                          for k in ps.get("required", [])]
    bridge = synthesize_bridge(SemanticPort("session-output", "output", "output", mapped),
                               SemanticPort("session-input", "input", "input", cs),
                               allow_lossy=bool(drops))
    if bridge["status"] != "candidate":
        return "NEGOTIATE", ["EXISTING_BRIDGE_REJECTED"], None
    adapter = _seal({"semanticMapping": mapping, "semanticOperations": operations,
                     "structuralBridge": bridge, "droppedFields": drops}, "adapterRoot")
    outcome = "DEGRADE" if drops else ("ADAPT" if operations else "DIRECT")
    return outcome, ["EXPLICIT_SEMANTICS_AND_SCHEMA_PROOF"], adapter


def negotiate_session(producer, consumer, *, goal, available_authority=(), allowed_drops=()):
    """Different RCP capability IDs may compose; no authority is granted.

    NEGOTIATE has no executable contract: provide missing semantic/policy evidence
    and resubmit. DEGRADE requires exact, explicit source-field drop consent.
    """
    producer, consumer = deepcopy(producer), deepcopy(consumer)
    outcome, reasons, adapter = _plan(producer, consumer, goal, available_authority, allowed_drops)
    contract = None
    if adapter is not None:
        contract = _seal({"format": "taowind.opp.session-contract.v0.1",
            "profile": SESSION_PROFILE, "outcome": outcome, "goal": goal,
            "producer": producer, "consumer": consumer, "adapter": adapter,
            "availableAuthority": sorted(set(available_authority)),
            "allowedDrops": sorted(set(allowed_drops)), "authorityGranted": False,
            "boundary": "Candidate declaration agreement; caller owns provider trust, authority and transport. No implicit retries."},
            "contractRoot")
    return _seal({"format": "taowind.opp.session-negotiation.v0.1", "outcome": outcome,
                  "reasons": reasons, "contract": contract, "authorityGranted": False}, "negotiationRoot")


def verify_session_contract(contract, *, expected_root=None):
    _check_root(contract, "contractRoot", expected_root)
    regenerated = negotiate_session(contract["producer"], contract["consumer"],
        goal=contract["goal"], available_authority=contract["availableAuthority"],
        allowed_drops=contract["allowedDrops"])["contract"]
    if contract != regenerated:
        raise SessionError("CONTRACT_PLAN_NOT_REPRODUCIBLE")
    return True


@dataclass(frozen=True)
class SurfaceProvider:
    """Caller-installed transport binding, never constructed from remote code.

    describe must rediscover the current surface; invoke must enforce transport
    deadlines/output bounds and raise on remote errors. Returning stale discovery
    or ignoring transport failures violates this provider contract.
    """
    binding_id: str
    describe: Callable
    invoke: Callable


def _validate(value, schema, stage):
    if not Draft202012Validator(schema).is_valid(value):
        raise SessionError(f"{stage}_SCHEMA_REJECTED")
    content_root(value)  # Also forbid non-JSON / NaN outputs.


def _transform(contract, value):
    adapter = contract["adapter"]
    return apply_transform(apply_transform(value, adapter["semanticOperations"]),
                           adapter["structuralBridge"]["operations"])


def run_session(contract, producer_input, *, providers, allow_execution=False,
                available_authority=()):
    """Execute once with fresh discovery, schema checks and a rooted stage journal."""
    if not allow_execution:
        raise SessionError("EXECUTION_CONSENT_REQUIRED")
    contract, producer_input = deepcopy(contract), deepcopy(producer_input)
    verify_session_contract(contract)
    required = set(contract["producer"]["payload"]["authorityRequired"]) | set(
        contract["consumer"]["payload"]["authorityRequired"])
    if required - set(available_authority):
        raise SessionError("AUTHORITY_GAP")
    steps, output, error = [], None, None
    stage = "discovery"
    try:
        selected = {}
        for role in ("producer", "consumer"):
            declaration = contract[role]
            binding = declaration["extensions"]["session"]["surface"]["bindingId"]
            provider = providers[binding]
            if provider.binding_id != binding:
                raise SessionError("PROVIDER_BINDING_MISMATCH")
            current = provider.describe()
            if content_root(current) != content_root(declaration):
                raise SessionError(f"CAPABILITY_DRIFT:{role}")
            selected[role] = provider
            steps.append({"stage": f"discover-{role}", "declarationRoot": content_root(current)})
        stage = "producer-input"
        _validate(producer_input, contract["producer"]["payload"]["inputSchema"], "PRODUCER_INPUT")
        stage = "producer-call"
        value = selected["producer"].invoke(deepcopy(producer_input))
        stage = "producer-output"
        steps.append({"stage": "producer-output", "value": deepcopy(value), "valueRoot": content_root(value)})
        _validate(value, contract["producer"]["payload"]["outputSchema"], "PRODUCER_OUTPUT")
        stage = "adapter"
        transformed = _transform(contract, value)
        _validate(transformed, contract["consumer"]["payload"]["inputSchema"], "CONSUMER_INPUT")
        steps.append({"stage": "adapter", "value": deepcopy(transformed), "valueRoot": content_root(transformed)})
        stage = "consumer-rediscovery"
        if content_root(selected["consumer"].describe()) != content_root(contract["consumer"]):
            raise SessionError("CAPABILITY_DRIFT:consumer")
        stage = "consumer-call"
        output = selected["consumer"].invoke(deepcopy(transformed))
        stage = "consumer-output"
        steps.append({"stage": "consumer-output", "value": deepcopy(output), "valueRoot": content_root(output)})
        _validate(output, contract["consumer"]["payload"]["outputSchema"], "CONSUMER_OUTPUT")
    except Exception as exc:
        error = {"stage": stage, "code": str(exc) if isinstance(exc, SessionError) else type(exc).__name__,
                 "executionMayHaveOccurred": stage not in {"discovery", "producer-input"}}
        output = None
    return _seal({"format": "taowind.opp.session-receipt.v0.1", "contractRoot": contract["contractRoot"],
        "input": producer_input, "inputRoot": content_root(producer_input), "steps": steps,
        "status": "FAIL" if error else "PASS", "error": error, "result": output,
        "resultRoot": content_root(output), "authorityGranted": False, "implicitRetries": 0,
        "boundary": "Provider-reported execution, not authenticated or independent runtime attestation. Failed calls may have executed; no automatic retry or rollback."},
        "receiptRoot")


def verify_session_receipt(contract, receipt, *, expected_contract_root, expected_receipt_root):
    """Offline successful-chain verification, with externally supplied root pins.

    Checks consistency, not signer identity, authority, wall time or physical execution.
    Failed journals can be inspected but are never accepted as successful evidence.
    """
    verify_session_contract(contract, expected_root=expected_contract_root)
    if not Draft202012Validator(read_json_resource("schemas/session-artifacts.schema.json")).is_valid(receipt):
        raise SessionError("RECEIPT_SCHEMA_INVALID")
    _check_root(receipt, "receiptRoot", expected_receipt_root)
    if (receipt.get("format") != "taowind.opp.session-receipt.v0.1" or
            receipt.get("contractRoot") != contract["contractRoot"] or receipt.get("status") != "PASS"
            or receipt.get("error") is not None or receipt.get("authorityGranted") is not False
            or receipt.get("implicitRetries") != 0):
        raise SessionError("RECEIPT_NOT_SUCCESSFUL_BOUND_SESSION")
    steps = receipt["steps"]
    if [s["stage"] for s in steps] != ["discover-producer", "discover-consumer", "producer-output", "adapter", "consumer-output"]:
        raise SessionError("RECEIPT_STAGE_SEQUENCE_INVALID")
    for index, role in enumerate(("producer", "consumer")):
        if steps[index]["declarationRoot"] != content_root(contract[role]):
            raise SessionError("DISCOVERY_ROOT_MISMATCH")
    _validate(receipt["input"], contract["producer"]["payload"]["inputSchema"], "PRODUCER_INPUT")
    for step, schema in zip(steps[2:], (contract["producer"]["payload"]["outputSchema"],
            contract["consumer"]["payload"]["inputSchema"], contract["consumer"]["payload"]["outputSchema"])):
        _validate(step["value"], schema, step["stage"])
        if content_root(step["value"]) != step["valueRoot"]:
            raise SessionError("STAGE_VALUE_ROOT_MISMATCH")
    if (_transform(contract, steps[2]["value"]) != steps[3]["value"] or
            receipt["result"] != steps[4]["value"] or
            receipt["inputRoot"] != content_root(receipt["input"]) or
            receipt["resultRoot"] != content_root(receipt["result"])):
        raise SessionError("RECEIPT_DATAFLOW_MISMATCH")
    return True
