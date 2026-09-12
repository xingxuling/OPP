# Public SDK candidate, API surface 1

Install a wheel in your own environment. Python 3.10+ is required.

```powershell
python -m pip wheel --no-deps . -w dist
python -m venv .venv
.venv/Scripts/python -m pip install dist/taowind_opp-0.3.0.dev1-py3-none-any.whl
```

Application imports use `opp.sdk`. It re-exports existing OPP implementations;
OPP continues to own discovery, compatibility, transformations and execution
receipts. Existing `opp`, `opp.bridge`, `opp.runtime` and CLI imports remain valid.
`SDK_API_VERSION == 1` identifies this public surface, not a production or 1.0
stability claim. Future incompatible public changes require a new major SDK
surface; fail-closed correctness fixes may reject previously accepted invalid data.

```python
from opp.sdk import verify_repository_semantics, plan_repository_connection

producer = verify_repository_semantics("/path/to/producer")
consumer = verify_repository_semantics("/path/to/consumer")
report = plan_repository_connection(producer, consumer, include_rejected=True)
print(report["acceptedPlanCount"])
```

Scanning does not execute source. Missing annotations remain unknown; class methods,
decorator registration, MCP discovery and arbitrary OpenAPI are not automatically
converted into executable providers. A positive shape comparison does not prove
business semantics. See the real [external library experiment](EXTERNAL_ONBOARDING.md).

For explicitly reviewed native calls, use `InvocationSpec`, `SemanticPort`,
`synthesize_bridge`, `run_invocation` and `run_interop` from the same namespace.
Execution requires `allow_execution=True` (or CLI `--allow-execution`). SourceRoot
must be supplied by the caller. No ambient credential or authority is inherited.
The bounded Python child is not an OS security sandbox.

## Offline verification

Keep the original run specification and input separately from the result. Then:

```powershell
python -m opp interop verify run-spec.json input.json result.json
```

Or call `verify_interop_result(result, run_spec, input)` from `opp.sdk`. It returns
True or raises `InteropError`; it never starts the target, opens a network
connection or retries. Verification binds schema, receipt roots, original input,
invocation specs, plan content, transformed value and final result. A modified plan
is rejected before execution. Timing is diagnostic and excluded from OPP roots.

Only successful results are accepted by this API. FAIL artifacts remain failure
diagnostics; do not interpret their rejection here as evidence that no work occurred.
Retaining hashes alone does not authenticate an operator: replacing all inputs,
results and expected hashes can still forge a self-consistent story. Independent
operator signatures and trusted checkpoints remain external responsibilities.

## Replay three real projects

```powershell
.venv/Scripts/python -m pip install -r examples/external-projects/requirements.txt
.venv/Scripts/python -I scripts/verify_external_projects.py --out C:/new/opp-evidence
```

Run this with the installed wheel, not an editable checkout. Output must be a new
directory. The script never downloads or installs dependencies. Each record retains
the reviewed adapter, installed package versions/file hashes, discovered interfaces,
manual contract, synthesized plan, successful execution, real-library failure and
explicit successful re-invocation. Production retries and crash recovery are outside
this stateless experiment. Capture the entire generated directory for review.

`scripts/verify_external_projects.py` and the example are checkout tools; the
`opp.sdk` API and `opp interop verify` are included in the wheel.
