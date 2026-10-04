"""Producer -> OPP Bridge -> Consumer interoperability runner（生产端→OPP桥→消费端互操作运行器）。"""
from __future__ import annotations
from typing import Any
from ..bridge.transform import apply_transform, TransformError
from ..integrity import content_root, LEGACY_CANONICAL_PROFILE, native_receipt_format
from .invoke import run_invocation, InvocationError

class InteropError(RuntimeError):
    pass


def _bridge_plan_body(bridge):
    # Auto Connect appends these source descriptors after synthesize_bridge seals
    # the executable plan. They are bound by reportRoot, not the inner planRoot.
    # Execution targets remain bound separately in the invocation specifications.
    return {k: v for k, v in bridge.items()
            if k not in {'planRoot', 'producerInterface', 'consumerInterface'}}


def run_interop(run_spec: dict[str, Any], producer_input: Any, *, allow_execution: bool = False, canonical_profile: str = LEGACY_CANONICAL_PROFILE) -> dict[str, Any]:
    if not allow_execution:
        raise InteropError("EXECUTION_CONSENT_REQUIRED")
    try:
        native_receipt_format("interop", canonical_profile)
    except ValueError as exc:
        raise InteropError(str(exc)) from exc
    if not isinstance(run_spec, dict) or run_spec.get("format") != "taowind.opp.interop-run.v0.1":
        raise InteropError("INTEROP_RUN_SPEC_INVALID")
    bridge = run_spec.get("bridgePlan") or {}
    if bridge.get("status") != "candidate":
        raise InteropError("BRIDGE_PLAN_NOT_EXECUTABLE_CANDIDATE")
    if bridge.get("executionModel") != "opp-declarative-json-transform":
        raise InteropError("BRIDGE_EXECUTION_MODEL_UNSUPPORTED")
    if bridge.get("planRoot") != content_root(_bridge_plan_body(bridge)):
        raise InteropError("BRIDGE_PLAN_ROOT_INVALID")
    producer = run_invocation(run_spec.get("producer") or {}, producer_input, allow_execution=True, canonical_profile=canonical_profile)
    if producer["receipt"]["status"] != "PASS":
        return _interop_receipt(run_spec, producer_input, producer=producer, transformed=None, consumer=None, status="FAIL", error="PRODUCER_FAILED", canonical_profile=canonical_profile)
    try:
        transformed = apply_transform(producer["result"], bridge.get("operations") or [])
    except TransformError as exc:
        return _interop_receipt(run_spec, producer_input, producer=producer, transformed=None, consumer=None, status="FAIL", error=f"BRIDGE_FAILED:{exc}", canonical_profile=canonical_profile)
    consumer = run_invocation(run_spec.get("consumer") or {}, transformed, allow_execution=True, canonical_profile=canonical_profile)
    status = "PASS" if consumer["receipt"]["status"] == "PASS" else "FAIL"
    return _interop_receipt(run_spec, producer_input, producer=producer, transformed=transformed, consumer=consumer, status=status, error=None if status=="PASS" else "CONSUMER_FAILED", canonical_profile=canonical_profile)


def _interop_receipt(run_spec: dict[str, Any], producer_input: Any, *, producer: dict | None, transformed: Any, consumer: dict | None, status: str, error: str | None, canonical_profile: str = LEGACY_CANONICAL_PROFILE) -> dict[str, Any]:
    root = lambda value: content_root(value, profile=canonical_profile)
    stable = {
        "format": native_receipt_format("interop", canonical_profile),
        "version": "0.3.0-candidate.1",
        "runId": str(run_spec.get("runId") or "interop-run"),
        "status": status,
        "producerRequestRoot": root(producer_input),
        "producerReceiptRoot": producer["receipt"]["receiptRoot"] if producer else None,
        "bridgePlanRoot": (run_spec.get("bridgePlan") or {}).get("planRoot"),
        "transformedRoot": root(transformed) if transformed is not None else None,
        "consumerReceiptRoot": consumer["receipt"]["receiptRoot"] if consumer else None,
        "finalResultRoot": root(consumer["result"]) if consumer and consumer.get("result") is not None else None,
        "error": error,
        "authority": {"promotionPerformed": False, "environmentAuthorityInherited": False},
        "executionBoundary": {"explicitConsentRequired": True, "strongOsSandboxClaimed": False, "hiddenRetries": False},
        "boundary": "Interop PASS proves only this concrete producer/bridge/consumer run. It does not establish universal compatibility, target safety, or strong OS isolation / 互操作 PASS 只证明本次具体生产端/桥/消费端运行成功，不代表普遍兼容、目标安全或强操作系统隔离。",
    }
    if canonical_profile != LEGACY_CANONICAL_PROFILE:
        stable["canonicalProfile"] = canonical_profile
    return {
        "receipt": {**stable, "receiptRoot": root(stable)},
        "producer": producer,
        "transformed": transformed,
        "consumer": consumer,
        "result": consumer.get("result") if consumer else None,
    }
