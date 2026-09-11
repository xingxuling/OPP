# Integration Court — Windows UTF-8 Boundary

## Current Reality

- Repository: `xingxuling/OPP`
- Audited base: `main@61cc3828a58a7bffa8b1dbeb8c44ff3a9cb471d1`
- Candidate branch: `codex/opp-windows-utf8-v01`
- Scope: OPP host/runtime encoding boundary only. RCL ownership and protocol IDs are unchanged.
- Baseline: 41 tests; 37 passed and 4 CLI tests failed because Windows `cp950` could not encode bilingual JSON output.

## What Changed

1. `src/opp/runtime/child_python.py` now reads stdin and emits the child receipt through explicit UTF-8 byte boundaries. This is required because Python `-I` ignores `PYTHON*` environment variables.
2. `src/opp/cli.py` emits ASCII-safe JSON on stdout and protects help/diagnostic output with a locale-safe error handler. `--out` files remain UTF-8.
3. `tests/test_native_interop.py` adds a non-ASCII invocation payload test and a legacy-code-page CLI output test.

## Evidence

- Machine evidence: `evidence/OPP_WINDOWS_UTF8_AUDIT_2026-09-11.json`
- RCL stress ledger: `docs/RCL_STRESS_FIELD_2026-09-11.md`
- Evidence root: `132751eecd2a7f220ca29eb61b98356f532910e3e9e2431c559ea7307f6812a7`
- Source boundary: `src/opp/cli.py`, `src/opp/runtime/child_python.py`
- Concrete interop receipt root: `77b4cdfaa0f95a9cc75a4c7d08f9d8cc3b94d40f2a9b46b87c51b2b1496f7ff2`
- Wheel evidence: the patched `taowind-opp==0.3.0.dev1` wheel was force-installed into an isolated virtual environment; installed `opp validate` and a Chinese-payload invocation both exited successfully under `PYTHONIOENCODING=cp950`.

## Tests

- `python -m unittest discover -s tests -v`: `43/43 PASS` on the Windows host.
- `python -m compileall -q src`: `PASS`.
- CLI validation and example `Producer → Bridge → Consumer` interop under the default Windows locale: `PASS`.
- Wheel build and forced isolated installation: `PASS`.

## Claims Promoted

- OPP's candidate Python child invocation now has locally verified UTF-8 payload transport on this Windows host.
- OPP's candidate CLI JSON output now remains parseable under the tested legacy Windows code page.

These are local candidate/runtime claims only; no protocol status or authority was promoted.

## Claims Still Forbidden

- No claim of strong OS sandboxing, network isolation, filesystem isolation, or malicious-code safety.
- No claim of independent third-party interoperability.
- No claim of cross-host, staging, production, external standard, or CI verification.
- No authority promotion, canonical promotion, or RCL ownership change.

## Remaining Production Gaps

`OPP-THIRD-PARTY-001`, `OPP-SANDBOX-001`, and `OPP-DISTRIBUTED-001` remain open. The source still uses a bounded child process, not a strong sandbox, and still has no independent third-party or cross-host evidence.

## Next Frontier

Select one structurally unfamiliar third-party producer/consumer and run a consented, receipt-producing interoperability experiment. Keep the result `THIRD_PARTY_VERIFIED` only if the external system is genuinely independent and the evidence is reproducible.

## Merge / Release Decision

Candidate branch is ready for review after local verification. Do not label the package production-ready or stable; merge requires review of the evidence, the RCL stress ledger, and the remaining sandbox/distributed/third-party boundaries.
