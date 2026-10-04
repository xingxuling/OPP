"""Offline verification bound to caller-retained inputs, without re-execution."""
from ..integrity import content_root, LEGACY_CANONICAL_PROFILE, native_receipt_format
from ..bridge.transform import apply_transform
from .interop import InteropError, _interop_receipt, _bridge_plan_body
from .model import InvocationSpec
from .invoke import _receipt_core
from ..registry import read_json_resource
from jsonschema import Draft202012Validator


def _require(ok, code):
    if not ok:
        raise InteropError(code)


def verify_interop_result(result, run_spec, producer_input, *, canonical_profile=LEGACY_CANONICAL_PROFILE):
    """Verify a successful interop result against separately retained inputs.

    Hash consistency is not a signature or independent proof of execution.
    FAIL results remain diagnostic evidence, never successful acceptance.
    """
    try:
        native_receipt_format('interop', canonical_profile)
        root = lambda value: content_root(value, profile=canonical_profile)
        suffix = '' if canonical_profile == LEGACY_CANONICAL_PROFILE else '.v0.2'
        _require(run_spec.get('format') == 'taowind.opp.interop-run.v0.1', 'INTEROP_RUN_SPEC_INVALID')
        _require(set(result) == {'receipt', 'producer', 'transformed', 'consumer', 'result'}, 'INTEROP_RESULT_SHAPE')
        _require(Draft202012Validator(read_json_resource(f'schemas/interop-receipt{suffix}.schema.json')).is_valid(result['receipt']), 'INTEROP_RECEIPT_SCHEMA')
        _require(result['receipt']['status'] == 'PASS', 'INTEROP_SUCCESS_REQUIRED')
        plan = run_spec['bridgePlan']
        _require(plan['planRoot'] == content_root(_bridge_plan_body(plan)), 'BRIDGE_PLAN_ROOT_INVALID')
        _require(plan['status'] == 'candidate' and plan['executionModel'] == 'opp-declarative-json-transform', 'BRIDGE_PLAN_NOT_EXECUTABLE_CANDIDATE')
        for role, value in [('producer', producer_input), ('consumer', result['transformed'])]:
            invocation = result[role]
            receipt = invocation['receipt']
            _require(Draft202012Validator(read_json_resource(f'schemas/invocation-receipt{suffix}.schema.json')).is_valid(receipt), 'INVOCATION_RECEIPT_SCHEMA')
            spec = InvocationSpec.from_dict(run_spec[role])
            _require(receipt['status'] == 'PASS' and receipt['exitCode'] == 0
                     and receipt['timedOut'] is False and receipt['error'] is None, 'INVOCATION_SUCCESS_REQUIRED')
            stable = {k: v for k, v in receipt.items() if k not in {'receiptRoot', 'durationMs'}}
            _require(receipt['receiptRoot'] == root(stable), 'INVOCATION_RECEIPT_ROOT_INVALID')
            expected_core = _receipt_core(spec, root(value), status='PASS', exit_code=0,
                timed_out=False, result_root=root(invocation['result']),
                stdout_bytes=receipt['stdoutBytes'], stderr_bytes=receipt['stderrBytes'],
                target_stdout=receipt['targetStdout'], target_stderr=receipt['targetStderr'], error=None, canonical_profile=canonical_profile)
            _require(stable == expected_core, 'INVOCATION_RECEIPT_FIELDS_INVALID')
            _require(receipt['requestRoot'] == root({'spec': spec.to_dict(), 'inputRoot': root(value)}), 'INVOCATION_REQUEST_ROOT_INVALID')
            _require(receipt['resultRoot'] == root(invocation['result']), 'INVOCATION_RESULT_ROOT_INVALID')
        _require(root(apply_transform(result['producer']['result'], plan['operations'])) == root(result['transformed']), 'INTEROP_TRANSFORM_MISMATCH')
        expected = _interop_receipt(run_spec, producer_input, producer=result['producer'],
                                   transformed=result['transformed'], consumer=result['consumer'], status='PASS', error=None, canonical_profile=canonical_profile)
        _require(result['receipt'] == expected['receipt'] and result['result'] == expected['result'], 'INTEROP_RESULT_MISMATCH')
        return True
    except InteropError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise InteropError('INTEROP_VERIFICATION_INVALID') from exc
