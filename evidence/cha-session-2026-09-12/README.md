# CHA Session evidence ledger — 2026-09-12

Verdict: **VERIFIED_LOCAL_CANDIDATE** for the bounded two-party session profile.
Baseline: OPP main `2e067522e2b79d927569be02a423c58ebbca268e`.
Branch: `codex/opp-cha-session-v01`. No production/authority/independent-operator promotion.

## Verified execution

- [65/65 source regression tests](tests.log); the original 45 remain passing.
- New wheel built and installed in a fresh venv. Demo executed from outside the source checkout with Python `-I`, enforcing a site-packages OPP import.
- [Installed-wheel summary](installed-wheel/summary.json): Python 3.11.6, Windows, library/package versions and source hashes, timing, automatic/manual boundaries.
- Wheel SHA-256: `8f93268da91b57edb9dfc3d525126f74b1557aab2fb24771d06b2e1d257432d8`.
- Summary SHA-256: `445454ae2bb3662da69b58b347196a311669cfaf5703ea7dc40b6f36aa7b3667`.
- Offline verifier under that explicit summary pin: **PASS**, two successful sessions plus explicit recovery. The pin must be independently retained for independent tamper protection.
- [Post-commit archive check](post-commit-check.json): evidence bytes and actor source hashes match the committed archive exactly; four wheel text files match Git source after CRLF/LF normalization. No reproducible-wheel claim.

| Maintained external project | Actual surface/run | Automatically identified | Manual work | Failure/recovery boundary | Evidence |
|---|---|---|---|---|---|
| Boltons 26.2.0 | existing OPP Python child, unique_numbers | native signature scan; exported input/output shapes; field concept match | wrapper, JSON contract and concept/unit assertion | participates in HTTP failure chain and explicit rerun; no physical host failure injected | native-discovery, native-invocation-receipts, boltons-source |
| JMESPath 1.1.0 | loopback HTTP/OpenAPI, sort_sequence | fetched operation ID and request/response schemas | server wrapper; semantic assertion; registered HTTP provider | real HTTP 503, consumer-call FAIL, explicit healthy-provider rerun PASS | openapi-discovery, surface-calls, http-failure, http-recovery |
| more-itertools 11.1.0 | real JSON stdin/stdout process, chunk_pairs | CLI --describe schemas; semantic rename ordered→entries | CLI wrapper; descriptor conventions; semantic assertion | positive invocation; no CLI crash/restart recovery claimed in this run | cli-discovery, http-cli-receipt, more-itertools-source |

Measured automated session elapsed times: Python→HTTP **647.94 ms**, HTTP→CLI **1058.16 ms**. These include local discovery/calls/verification. Human integration time was **NOT_MEASURED**; these are not onboarding-time or production-performance claims. See the summary for exact values and total run time.

The libraries have separate upstream maintainers. Their wrappers and all OPP peers here share one author/operator and one physical machine. This is real library and heterogeneous surface execution, not three independent implementations of OPP. The earlier external-onboarding corpus remains historical evidence, not substituted for this run.

## Complete chain

1. Raw native/CLI descriptors and HTTP OpenAPI fetched from running actors.
2. CHP accepts common OPP semantics with **zero shared business capability IDs**.
3. RCP declarations retain different operation IDs and field names.
4. Negotiation generates ADAPT contracts, mapping `unique_items→values` and `ordered→entries` from explicit matching concepts/units.
5. Existing OPP declarative transforms execute; actual outputs are `{ordered:[1,2,3]}` and `{groups:[[1,2],[3]]}`.
6. Contract, discovery, input, bridge/mapping, intermediate and final output roots verify offline. Raw artifacts are byte-hashed by the summary.

Read [python-http-negotiation](installed-wheel/python-http-negotiation.json), [python-http-receipt](installed-wheel/python-http-receipt.json), [http-cli-negotiation](installed-wheel/http-cli-negotiation.json), [http-cli-receipt](installed-wheel/http-cli-receipt.json), [HTTP failure](installed-wheel/http-failure.json) and [recovery](installed-wheel/http-recovery.json).

Reproduce with [run_demo.py](../../examples/cha-session/run_demo.py); use a new output directory. Verify without executing providers:

```powershell
python scripts/verify_cha_session.py evidence/cha-session-2026-09-12/installed-wheel --expected-summary-sha256 445454ae2bb3662da69b58b347196a311669cfaf5703ea7dc40b6f36aa7b3667
```

## Integration Court / license / RCL stress

Reality audit and reuse decisions are in [CHA_SESSION.md](../../docs/CHA_SESSION.md). Product: callers can connect different business IDs. Semantic gate: missing meaning and unproven constraints stay unexecutable. Engineering: existing RCP/CHP/bridge/native runtime reused. Security: consent, scopes, drift, rehashed plan tamper, output schemas, no implicit retry tested. Evidence gate: installation and actual call results preserved. These are review concerns exercised by this run, not claims that independent reviewers or named autonomous agents participated.

License audit: OPP remains MIT; no dependency source was copied into core. Boltons installed LICENSE was reviewed (BSD-3-Clause terms), JMESPath metadata reports MIT, more-itertools and existing jsonschema report MIT. Existing third-party collector preserves installed file and license-file hashes in the three `*-source.json` files. Dependency versions remain the existing pinned external-project requirements. Package hashes prove provenance consistency, not independent authorship attestation.

RCL stress record:

- Task: negotiate heterogeneous capability declarations without silent semantic changes.
- Ownership: OPP owns compatibility/session/bridge meaning; TINP owns transport authority/routing/failover. Existing RCL admission/profile ownership unchanged.
- RCL_GAP decision: **NO_NEW_CORE_GAP_PROVEN**. This is OPP provider/tooling composition, not evidence that RCL could not express a required primitive.
- Missing product capabilities: independent surface acceptance, rich constraint inclusion proof, remote version preconditions. Workaround: bounded explicit assertions plus NEGOTIATE/REJECT; no alternate canonical owner.
- Donor advantage: OpenAPI exposes operation/body contracts; maintained libraries provide proven domain algorithms; Python/HTTP/CLI execute through existing or explicitly registered Providers.
- Gap type: provider interoperability / evidence; generality: cross-project candidate; candidate absorption: **NOT_PROPOSED** pending actual repeated RCL stress evidence.
- Stress/regression cases: same name with different meaning, unit mismatch, unknown schema/ref, required vs optional field, lossy consent, interface drift before and between calls, rehashed adapter tamper, HTTP failure with possible execution.
- Proposed K400 mapping: `windows::cli` K042, `server::web` K104, `distributed-runtime::distributed` K250 (future independent-host gate), `automation-runtime::agent` K354. No canonical matrix write or promotion performed.
- EXPRESS / COMPILE / LOWER / EXECUTE / CORRECT / ROBUST / PERFORMANCE / AI_GENERATE / EVIDENCE: **all NOT_ADJUDICATED in canonical K400**. Python execution and tests support this OPP candidate only; they do not compensate any RCL gate.

Open external gates: independent operator/security review, physical multi-host, Authority Provider, trusted time/key lifecycle, production transport, independently maintained MCP server invocation. gRPC and multi-party protocol negotiation remain unimplemented. No actual account or hardware was needed for this bounded round.
