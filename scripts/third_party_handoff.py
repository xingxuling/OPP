"""Verify a TINP HTTP observation receipt before invoking an OPP consumer."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from opp.integrity import content_root
from opp.runtime.invoke import InvocationError, run_invocation

HASH = re.compile(r"^[0-9a-f]{64}$")
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
RUN_FORMAT = "twni.opp-http-readonly-run.v1"
RECEIPT_FORMAT = "twni.opp-http-readonly-receipt.v1"
RECEIPT_BOUNDARY = "Read-only external observation; no credential, retry, redirect, or authority grant"
RUN_BOUNDARY = "The adapter proves only this explicit read-only request; it grants no authority or general network access"
RUN_KEYS = {"format", "status", "policyRoot", "requestRoot", "response", "receipt", "boundary"}
RECEIPT_KEYS = {
    "format", "policyRoot", "requestRoot", "status", "httpStatus", "responseContentType",
    "responseEtag", "responseLastModified", "responseBytes", "wireResponseRoot",
    "responseRoot", "error", "attempts", "redirectsFollowed", "ambientProxyUsed",
    "ambientCredentialsUsed", "authorityGranted", "boundary", "receiptRoot",
}


def load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def is_hash(value: Any) -> bool:
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def is_clean_text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 4096 and value.strip() == value and not re.search(r"[\x00-\x1f\x7f]", value)


def is_json_content_type(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    media_type = value.split(";", 1)[0].strip().lower()
    return media_type == "application/json" or media_type.endswith("+json")


def verify_provider_handoff(value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    require(isinstance(value, dict) and set(value) == RUN_KEYS, "TINP_HANDOFF_SHAPE_INVALID")
    require(value.get("format") == RUN_FORMAT, "TINP_HANDOFF_FORMAT_INVALID")
    require(value.get("status") == "PASS" and value.get("boundary") == RUN_BOUNDARY, "TINP_HANDOFF_PROVIDER_NOT_PASS")
    require(is_hash(value.get("policyRoot")) and is_hash(value.get("requestRoot")), "TINP_HANDOFF_ROOT_INVALID")
    response = value.get("response")
    receipt = value.get("receipt")
    require(isinstance(response, dict) and isinstance(receipt, dict), "TINP_HANDOFF_RESPONSE_REQUIRED")
    require(set(receipt) == RECEIPT_KEYS, "TINP_HANDOFF_RECEIPT_SHAPE_INVALID")
    receipt_root = receipt.get("receiptRoot")
    receipt_body = {key: item for key, item in receipt.items() if key != "receiptRoot"}
    require(is_hash(receipt_root)
            and content_root(receipt_body) == receipt_root, "TINP_HANDOFF_RECEIPT_ROOT_INVALID")
    require(receipt.get("format") == RECEIPT_FORMAT
            and receipt.get("status") == "PASS"
            and receipt.get("policyRoot") == value.get("policyRoot")
            and receipt.get("requestRoot") == value.get("requestRoot"), "TINP_HANDOFF_RECEIPT_BINDING_INVALID")
    require(type(receipt.get("httpStatus")) is int and 200 <= receipt["httpStatus"] <= 299
            and is_json_content_type(receipt.get("responseContentType"))
            and all(receipt.get(key) is None or is_clean_text(receipt.get(key)) for key in ("responseEtag", "responseLastModified"))
            and type(receipt.get("responseBytes")) is int and 0 <= receipt["responseBytes"] <= MAX_RESPONSE_BYTES
            and is_hash(receipt.get("wireResponseRoot"))
            and is_hash(receipt.get("responseRoot"))
            and receipt.get("error") is None, "TINP_HANDOFF_RECEIPT_SEMANTICS_INVALID")
    require(receipt.get("responseRoot") == content_root(response), "TINP_HANDOFF_RESPONSE_ROOT_INVALID")
    require(type(receipt.get("attempts")) is int and receipt.get("attempts") == 1
            and receipt.get("redirectsFollowed") is False
            and receipt.get("ambientProxyUsed") is False
            and receipt.get("ambientCredentialsUsed") is False
            and receipt.get("authorityGranted") is False
            and receipt.get("boundary") == RECEIPT_BOUNDARY, "TINP_HANDOFF_BOUNDARY_INVALID")
    return response, receipt


def make_result(value: dict[str, Any], response: dict[str, Any], provider_receipt: dict[str, Any], consumer: dict[str, Any]) -> dict[str, Any]:
    body = {
        "format": "taowind.opp.tinp-http-handoff.v0.1",
        "status": "PASS",
        "providerPolicyRoot": value["policyRoot"],
        "providerRequestRoot": value["requestRoot"],
        "providerReceiptRoot": provider_receipt["receiptRoot"],
        "providerResponseRoot": provider_receipt["responseRoot"],
        "consumerReceiptRoot": consumer["receipt"]["receiptRoot"],
        "consumerResultRoot": consumer["receipt"]["resultRoot"],
        "consumerResult": consumer["result"],
        "authority": {"promotionPerformed": False, "authorityGranted": False},
        "boundary": "This handoff proves one TINP policy-bound observation was accepted by one explicit OPP consumer; it does not prove general interoperability or production network authority.",
    }
    return {**body, "handoffRoot": content_root(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a TINP HTTP receipt before bounded OPP consumer execution")
    parser.add_argument("handoff")
    parser.add_argument("consumer_spec")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        value = load(args.handoff)
        response, provider_receipt = verify_provider_handoff(value)
        consumer = run_invocation(load(args.consumer_spec), response, allow_execution=True)
        if consumer["receipt"]["status"] != "PASS":
            raise ValueError(f"OPP_CONSUMER_FAILED:{consumer['receipt'].get('error') or 'UNKNOWN'}")
        result = make_result(value, response, provider_receipt, consumer)
        serialized = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
        if args.out:
            with Path(args.out).open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        else:
            sys.stdout.write(serialized)
        return 0
    except (OSError, ValueError, InvocationError) as exc:
        sys.stderr.write(f"{getattr(exc, 'code', None) or str(exc)}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
