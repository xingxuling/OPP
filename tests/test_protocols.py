from __future__ import annotations
import json, unittest
from pathlib import Path
from opp.handshake import negotiate_handshake
from opp.capability import negotiate_capability
from opp.integrity import seal_envelope, verify_envelope_root
from opp.registry import load_registry, repository_root
from opp.validation import validate_envelope

ROOT = repository_root()

class OPPTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_registry_has_six_core_protocols(self):
        reg = load_registry()
        self.assertEqual(6, len(reg["protocols"]))
        self.assertEqual({"RXP","RCP","RAP","REP","RSP","CHP"}, {p["short"] for p in reg["protocols"]})

    def test_all_examples_validate(self):
        for name in ["exchange.json","capability.json","artifact.json","evidence.json","state.json","handshake-dwac.json","handshake-rncs.json"]:
            with self.subTest(name=name):
                self.assertEqual([], validate_envelope(self.load(name)))

    def test_integrity_detects_tamper(self):
        env = self.load("capability.json")
        self.assertTrue(verify_envelope_root(env))
        env["payload"]["availability"] = "available"
        self.assertFalse(verify_envelope_root(env))
        self.assertTrue(any(i.code == "INTEGRITY_ROOT_MISMATCH" for i in validate_envelope(env)))

    def test_seal_is_deterministic_for_same_content(self):
        env = self.load("artifact.json")
        env.pop("integrity", None)
        a, b = seal_envelope(env), seal_envelope(env)
        self.assertEqual(a["integrity"]["contentRoot"], b["integrity"]["contentRoot"])

    def test_handshake_intersection_does_not_create_authority(self):
        a, b = self.load("handshake-dwac.json"), self.load("handshake-rncs.json")
        result = negotiate_handshake(a, b)
        self.assertEqual([], validate_envelope(result))
        self.assertEqual("accepted", result["payload"]["status"])
        self.assertEqual(["opp.chp.v0.1", "opp.rcp.v0.1", "opp.rep.v0.1"], result["payload"]["agreedProtocols"])
        self.assertEqual(["evidence.emit"], result["payload"]["sharedCapabilities"])
        self.assertEqual([], result["payload"]["authorityScopes"])
        self.assertEqual(0.8, result["payload"]["evidencePolicy"]["minimumConfidence"])
        self.assertFalse(result["payload"]["evidencePolicy"]["acceptDerivedEvidence"])

    def test_unknown_protocol_fails_closed(self):
        env = self.load("exchange.json")
        env.pop("integrity", None)
        env["protocol"] = "opp.unknown.v9"
        self.assertTrue(any(i.code == "PROTOCOL_UNKNOWN" for i in validate_envelope(env)))

    def test_capability_contract_negotiation_is_exact_and_non_authoritative(self):
        capability = self.load("capability.json")
        remote = json.loads(json.dumps(capability))
        remote["issuer"] = {"id": "rncs", "type": "runtime", "displayName": "rncs"}
        remote["id"] = "capability:rncs.structural.whole-artifact.compile.v1"
        remote["payload"]["capabilityId"] = capability["payload"]["capabilityId"]
        remote = seal_envelope({k: v for k, v in remote.items() if k != "integrity"})
        result = negotiate_capability(capability, remote)
        self.assertEqual("accepted", result["status"])
        self.assertEqual(capability["payload"]["capabilityId"], result["capabilityId"])
        self.assertFalse(result["authorityGranted"])
        self.assertTrue(result["contentRoot"])

    def test_capability_contract_negotiation_rejects_schema_drift(self):
        capability = self.load("capability.json")
        remote = json.loads(json.dumps(capability))
        remote["issuer"] = {"id": "rncs", "type": "runtime", "displayName": "rncs"}
        remote["payload"]["inputSchema"] = {"type": "object", "properties": {"extra": {"type": "string"}}}
        remote = seal_envelope({k: v for k, v in remote.items() if k != "integrity"})
        result = negotiate_capability(capability, remote)
        self.assertEqual("rejected", result["status"])
        self.assertIn("INPUT_SCHEMA_MISMATCH", result["reasons"])

if __name__ == "__main__":
    unittest.main()
