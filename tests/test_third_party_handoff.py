from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from opp.integrity import content_root
from scripts.third_party_handoff import verify_provider_handoff


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "examples/third-party-fixtures/tinp-http-handoff.json"


def load_handoff() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def reroot_receipt(value: dict) -> dict:
    receipt = value["receipt"]
    body = {key: item for key, item in receipt.items() if key != "receiptRoot"}
    receipt["receiptRoot"] = content_root(body)
    return value


class ThirdPartyHandoffTests(unittest.TestCase):
    def test_valid_tinp_handoff_passes_independent_opp_checks(self) -> None:
        response, receipt = verify_provider_handoff(load_handoff())
        self.assertEqual(response["full_name"], "xingxuling/OPP")
        self.assertEqual(receipt["httpStatus"], 200)

    def test_re_rooted_semantic_receipt_mutations_fail_closed(self) -> None:
        mutations = {
            "status": lambda receipt: receipt.update(httpStatus=500),
            "media": lambda receipt: receipt.update(responseContentType="text/html"),
            "error": lambda receipt: receipt.update(error="FORGED"),
            "size": lambda receipt: receipt.update(responseBytes=16 * 1024 * 1024 + 1),
            "boundary": lambda receipt: receipt.update(boundary="authority granted"),
            "attempts": lambda receipt: receipt.update(attempts=2),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                forged = copy.deepcopy(load_handoff())
                mutate(forged["receipt"])
                reroot_receipt(forged)
                with self.assertRaisesRegex(ValueError, "TINP_HANDOFF_"):
                    verify_provider_handoff(forged)

    def test_extra_receipt_field_cannot_hide_in_a_recomputed_root(self) -> None:
        forged = copy.deepcopy(load_handoff())
        forged["receipt"]["unexpected"] = True
        reroot_receipt(forged)
        with self.assertRaisesRegex(ValueError, "TINP_HANDOFF_RECEIPT_SHAPE_INVALID"):
            verify_provider_handoff(forged)


if __name__ == "__main__":
    unittest.main()
