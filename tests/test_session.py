from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from opp.registry import read_json_resource

from opp.sdk import (describe_surface, describe_openapi, describe_mcp_tool, content_root,
                     seal_envelope, negotiate_session, run_session, SurfaceProvider,
                     SessionError, verify_session_contract, verify_session_receipt,
                     negotiate_capability)


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def capability(name, field="value", *, unit="1", concept="quantity", extras=False):
    shape = obj(**{field: {"type": "integer"}})
    if extras:
        shape["properties"]["debug"] = {"type": "string"}
        shape["required"].append("debug")
    return describe_surface(participant=name, capability_id=name, input_schema=shape,
        output_schema=shape, surface={"kind": "test", "bindingId": name, "revision": "1",
                                    "discoveryRoot": content_root(shape)},
        semantics={"input": {field: {"concept": concept, "unit": unit}},
                   "output": {field: {"concept": concept, "unit": unit}}}, statefulness="stateless")


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.p, self.c = capability("old", "legacy"), capability("new", "modern")

    def negotiate(self, **kw):
        return negotiate_session(self.p, self.c, goal="new", **kw)

    def providers(self):
        return {"old": SurfaceProvider("old", lambda: self.p, lambda x: x),
                "new": SurfaceProvider("new", lambda: self.c, lambda x: x)}

    def test_five_outcomes_and_legacy_unchanged(self):
        self.assertEqual("rejected", negotiate_capability(self.p, self.c)["status"])
        self.assertEqual("ADAPT", self.negotiate()["outcome"])
        self.c = capability("new", "legacy")
        self.assertEqual("DIRECT", self.negotiate()["outcome"])
        self.c = capability("new", "unknown", concept="different")
        self.assertEqual("NEGOTIATE", self.negotiate()["outcome"])
        self.c = capability("new", "modern", unit="m")
        self.assertEqual("REJECT", self.negotiate()["outcome"])
        self.c, self.p = capability("new", "modern"), capability("old", "legacy", extras=True)
        self.assertIsNone(self.negotiate()["contract"])
        self.assertEqual("DEGRADE", self.negotiate(allowed_drops=["debug"])["outcome"])

    def test_protocol_schema_and_packaged_copy(self):
        schema = read_json_resource("schemas/session-artifacts.schema.json")
        packaged = Path(__file__).resolve().parents[1] / "src/opp/resources/schemas/session-artifacts.schema.json"
        self.assertEqual(schema, json.loads(packaged.read_text(encoding="utf-8")))
        validator = Draft202012Validator(schema)
        negotiation = self.negotiate()
        contract = negotiation["contract"]
        receipt = run_session(contract, {"legacy": 3}, providers=self.providers(), allow_execution=True)
        for artifact in (negotiation, contract, receipt):
            validator.validate(artifact)
        self.c = capability("new", unit="m")
        validator.validate(self.negotiate())

    def test_real_dataflow_and_offline_verifier(self):
        contract = self.negotiate()["contract"]
        receipt = run_session(contract, {"legacy": 7}, providers=self.providers(), allow_execution=True)
        self.assertEqual("PASS", receipt["status"])
        self.assertEqual({"modern": 7}, receipt["result"])
        self.assertTrue(verify_session_receipt(contract, receipt,
            expected_contract_root=contract["contractRoot"], expected_receipt_root=receipt["receiptRoot"]))
        changed = deepcopy(receipt)
        changed["steps"][3]["value"]["modern"] = 8
        changed["receiptRoot"] = content_root({k: v for k, v in changed.items() if k != "receiptRoot"})
        with self.assertRaises(SessionError):
            verify_session_receipt(contract, changed, expected_contract_root=contract["contractRoot"],
                                   expected_receipt_root=changed["receiptRoot"])

    def test_adapter_tamper_even_when_rehashed_rejected(self):
        contract = self.negotiate()["contract"]
        contract["adapter"]["semanticOperations"][0]["to"] = "other"
        contract["contractRoot"] = content_root({k: v for k, v in contract.items() if k != "contractRoot"})
        with self.assertRaisesRegex(SessionError, "NOT_REPRODUCIBLE"):
            verify_session_contract(contract)

    def test_consent_and_authority_checked_before_providers(self):
        contract = self.negotiate()["contract"]
        with self.assertRaisesRegex(SessionError, "CONSENT"):
            run_session(contract, {}, providers={})
        self.c["payload"]["authorityRequired"] = ["invoke:consumer"]
        self.c = seal_envelope(self.c)
        self.assertEqual("REJECT", self.negotiate()["outcome"])
        contract = self.negotiate(available_authority=["invoke:consumer"])["contract"]
        with self.assertRaisesRegex(SessionError, "AUTHORITY"):
            run_session(contract, {}, providers={}, allow_execution=True)

    def test_drift_before_execution_and_between_calls(self):
        contract = self.negotiate()["contract"]
        self.c["extensions"]["session"]["surface"]["revision"] = "2"
        self.c = seal_envelope(self.c)
        result = run_session(contract, {"legacy": 3}, providers=self.providers(), allow_execution=True)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("discovery", result["error"]["stage"])
        contract = self.negotiate()["contract"]
        providers = self.providers()
        def changing(x):
            self.c["extensions"]["session"]["surface"]["revision"] = "3"
            self.c = seal_envelope(self.c)
            return x
        providers["old"] = SurfaceProvider("old", lambda: self.p, changing)
        result = run_session(contract, {"legacy": 3}, providers=providers, allow_execution=True)
        self.assertEqual("consumer-rediscovery", result["error"]["stage"])

    def test_runtime_schema_failure_does_not_call_consumer(self):
        providers = self.providers()
        providers["old"] = SurfaceProvider("old", lambda: self.p, lambda x: {"legacy": "wrong"})
        providers["new"] = SurfaceProvider("new", lambda: self.c, lambda x: self.fail("consumer called"))
        result = run_session(self.negotiate()["contract"], {"legacy": 2}, providers=providers, allow_execution=True)
        self.assertEqual("PRODUCER_OUTPUT_SCHEMA_REJECTED", result["error"]["code"])
        self.assertEqual(0, result["implicitRetries"])

    def test_failed_call_is_not_silently_retried(self):
        providers, calls = self.providers(), []
        def fail(x):
            calls.append(x)
            raise RuntimeError("secret provider exception must not appear")
        providers["new"] = SurfaceProvider("new", lambda: self.c, fail)
        result = run_session(self.negotiate()["contract"], {"legacy": 2}, providers=providers, allow_execution=True)
        self.assertEqual(1, len(calls))
        self.assertEqual("RuntimeError", result["error"]["code"])
        self.assertTrue(result["error"]["executionMayHaveOccurred"])

    def test_unknown_constraints_and_nested_transform_do_not_become_compatible(self):
        for shape in ({}, {"$ref": "https://example.invalid/schema"},
                      {"type": ["integer", "null"]},
                      obj(modern={"type": "integer", "minimum": 10}),
                      obj(modern=obj(child={"type": "integer"}))):
            with self.subTest(shape=shape):
                self.c["payload"]["inputSchema"] = shape
                self.c = seal_envelope(self.c)
                self.assertIsNone(self.negotiate()["contract"])

    def test_no_name_based_semantic_guess(self):
        self.c = capability("new", "legacy", concept="another-quantity")
        self.assertEqual("NEGOTIATE", self.negotiate()["outcome"])
        self.c = capability("new", "legacy")
        self.c["extensions"]["session"]["semantics"] = {}
        self.c = seal_envelope(self.c)
        self.assertIsNone(self.negotiate()["contract"])

    def test_optional_producer_fields_and_rename_cycles(self):
        self.p["payload"]["outputSchema"]["required"] = []
        self.p = seal_envelope(self.p)
        self.assertEqual("NEGOTIATE", self.negotiate()["outcome"])
        self.p = capability("old", "legacy")
        self.p["payload"]["outputSchema"]["properties"]["modern"] = {"type": "integer"}
        self.p = seal_envelope(self.p)
        self.assertEqual("NEGOTIATE", self.negotiate()["outcome"])

    def test_property_named_title_is_not_discarded(self):
        self.p, self.c = capability("old", "title"), capability("new", "description")
        self.assertEqual("ADAPT", self.negotiate()["outcome"])

    def test_const_object_keys_are_not_treated_as_schema_annotations(self):
        self.p["payload"]["outputSchema"]["properties"]["legacy"] = {"type": "object", "properties": {},
            "additionalProperties": False, "const": {"description": "A"}}
        self.c["payload"]["inputSchema"]["properties"]["modern"] = {"type": "object", "properties": {},
            "additionalProperties": False, "const": {"description": "B"}}
        self.p, self.c = seal_envelope(self.p), seal_envelope(self.c)
        self.assertIsNone(self.negotiate()["contract"])

    def test_negotiate_then_resubmit_explicit_semantics(self):
        original = deepcopy(self.c)
        self.c["extensions"]["session"]["semantics"] = {}
        self.c = seal_envelope(self.c)
        first = self.negotiate()
        self.assertEqual("NEGOTIATE", first["outcome"])
        self.assertIsNone(first["contract"])
        self.c = original
        self.assertEqual("ADAPT", self.negotiate()["outcome"])

    def test_rehashed_wrong_receipt_format_and_wrong_pin_fail(self):
        contract = self.negotiate()["contract"]
        receipt = run_session(contract, {"legacy": 1}, providers=self.providers(), allow_execution=True)
        with self.assertRaisesRegex(SessionError, "EXPECTED_ROOT"):
            verify_session_receipt(contract, receipt, expected_contract_root="0" * 64,
                                   expected_receipt_root=receipt["receiptRoot"])
        receipt["format"] = "another-protocol"
        receipt["receiptRoot"] = content_root({k: v for k, v in receipt.items() if k != "receiptRoot"})
        with self.assertRaises(SessionError):
            verify_session_receipt(contract, receipt, expected_contract_root=contract["contractRoot"],
                                   expected_receipt_root=receipt["receiptRoot"])

    def test_unknown_state_and_unhandled_policy_negotiate(self):
        for key, value in (("statefulness", "unknown"), ("sideEffects", ["write"]), ("rights", {"purpose": "research"})):
            original = deepcopy(self.c)
            self.c["payload"][key] = value
            self.c = seal_envelope(self.c)
            self.assertEqual("NEGOTIATE", self.negotiate()["outcome"])
            self.c = original

    def test_malformed_profile_and_semantics_fail_closed(self):
        for replacement in ([], {"profile": "opp.session.v0.1", "surface": [], "semantics": {}},
                            {**self.c["extensions"]["session"], "semantics": {"input": {"modern": []}}}):
            with self.subTest(replacement=replacement):
                self.c["extensions"]["session"] = replacement
                self.c = seal_envelope(self.c)
                self.assertIsNone(self.negotiate()["contract"])

    def test_degrade_actually_projects_only_consented_fields(self):
        self.p = capability("old", "legacy", extras=True)
        contract = self.negotiate(allowed_drops=["debug"])["contract"]
        result = run_session(contract, {"legacy": 9, "debug": "discard"}, providers=self.providers(), allow_execution=True)
        self.assertEqual({"modern": 9}, result["result"])
        self.assertEqual("REJECT", self.negotiate(allowed_drops=["debug", "legacy"])["outcome"])


class SurfaceImportTests(unittest.TestCase):
    def test_mcp_missing_output_is_unknown_and_annotations_not_authority(self):
        d = describe_mcp_tool({"name": "a", "inputSchema": obj(), "annotations": {"readOnlyHint": True}},
            participant="m", surface={"bindingId": "m", "revision": "1"}, semantics={})
        self.assertIsNone(d["payload"]["outputSchema"])
        self.assertEqual("unknown", d["payload"]["statefulness"])
        self.assertEqual([], d["payload"]["authorityRequired"])

    def test_openapi_security_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, "POLICY"):
            describe_openapi({"openapi": "3.1.0", "security": [{"key": []}],
                              "paths": {"/run": {"post": {}}}}, path="/run")


if __name__ == "__main__":
    unittest.main()
