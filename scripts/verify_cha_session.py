"""Offline artifact verification with a separately supplied summary SHA-256 pin."""
import argparse
import hashlib
import json
from pathlib import Path

from opp.sdk import verify_session_receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-summary-sha256", required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    raw = (directory / "summary.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.expected_summary_sha256:
        raise ValueError("EXPECTED_SUMMARY_SHA256_MISMATCH")
    summary = json.loads(raw)
    for name, expected in summary["artifactSha256"].items():
        path = (directory / name).resolve()
        if path.parent != directory or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("ARTIFACT_HASH_OR_PATH_MISMATCH")
    for session, roots in summary["expectedRoots"].items():
        contract = json.loads((directory / (session + "-negotiation.json")).read_bytes())["contract"]
        receipt = json.loads((directory / (session + "-receipt.json")).read_bytes())
        verify_session_receipt(contract, receipt, expected_contract_root=roots["contractRoot"],
                               expected_receipt_root=roots["receiptRoot"])
    failure = json.loads((directory / "http-failure.json").read_bytes())
    recovery = json.loads((directory / "http-recovery.json").read_bytes())
    contract = json.loads((directory / "python-http-negotiation.json").read_bytes())["contract"]
    if failure["status"] != "FAIL" or failure["implicitRetries"] != 0:
        raise ValueError("FAILURE_NOT_RECORDED")
    verify_session_receipt(contract, recovery, expected_contract_root=contract["contractRoot"],
                           expected_receipt_root=recovery["receiptRoot"])
    print(json.dumps({"status": "PASS", "sessions": len(summary["expectedRoots"]),
                      "failurePreserved": True, "recoveryVerified": True,
                      "boundary": "Offline consistency under supplied hash pin; no execution or identity attestation."}))


if __name__ == "__main__":
    main()
