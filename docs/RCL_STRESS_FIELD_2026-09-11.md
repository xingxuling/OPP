# OPP RCL Stress Field — 2026-09-11

**Verdict:** `CANDIDATE_STRESS_INPUT_ONLY`

This ledger records product evidence as pressure input for the RCL Universal Stress Matrix. It does not declare a K400 cell, RCL Core promotion, protocol promotion, or production readiness.

## No Silent RCL Bypass

| Gap | Missing capability | Workaround / donor | Gap type | Canonical decision | Candidate K400 references |
|---|---|---|---|---|---|
| `OPP-WIN-UTF8-001` | Locale-independent native child and CLI byte boundaries | Explicit UTF-8 child bytes; ASCII-safe CLI stdout; UTF-8 `--out` files | Auxiliary host runtime / evidence | No RCL semantic gap; Python host runtime remains the lowering/provider | `K042` candidate reference only |
| `OPP-THIRD-PARTY-001` | Independently reproducible external producer/consumer execution | Host-only GitHub observation plus a real fail-closed OPP child receipt | External interoperability / provider boundary | No RCL semantic gap; no generic HTTP meaning is guessed | `K110`, `K250`, `K257` candidate references only |
| `OPP-TRANSPORT-001` | Declared network, proxy, credential and transport receipt policy | TINP archaeology; explicit adapter/version binding is still required | Auxiliary transport provider integration | TINP or a mature transport adapter owns network policy; OPP remains transport-agnostic | `K110`, `K250` candidate references only |
| OPP CHP/RCP ownership | Avoid duplicating protocol agreement in a transport project | Reuse OPP CHP/RCP through TINP's thin adapter | Existing owner dependency | OPP remains the single owner of protocol agreement semantics | `K117`, `K257` candidate references only |

The K400 references above are candidate stress locations observed in the surrounding TaoWind ledgers. They are not canonical cell adjudications by this repository.

## Donor advantage and provider boundary

TINP base `codex/next-internet-v01@1aa235d9f5718f87c959e275da10a7bf12d58e9f` provides reusable UDP/TCP/TLS loopback transport, TINP DATA framing, peer public-key admission, timeout/overload handling, and a thin OPP negotiation adapter. The follow-up candidate `codex/tinp-transport-policy-v01@678ea875d432adfe833dc390bd236bbf03b7c9bb` adds a policy-bound read-only HTTP provider, hardened receipt/response boundaries, a native `https.request` path with a per-request Agent, and one receipt-bound OPP consumer handoff. Neither branch provides physical cross-host or production network evidence.

AI001 `codex/fix-ai001-index-v02@d80cd08` was inspected as a source donor: `src/openapi-source-frontend.mjs` extracts one RCL capability spec per OpenAPI 3.x operation, but its own boundary explicitly excludes HTTP execution. No transport code was copied and no OpenAPI execution capability is promoted.

Decision: reuse through the explicit TINP↔OPP adapter and policy binding candidate; do not copy TINP transport into OPP Core and do not call this TaoWind-to-TaoWind handoff independent third-party interoperability.

## Regression cases

1. `WIN_CP950_CLI_JSON`: bilingual CLI output remains ASCII-safe and JSON-parseable under the tested legacy code page.
2. `ISOLATED_CHILD_UTF8_PAYLOAD`: a Chinese payload survives Python `-I` child execution without relying on `PYTHONIOENCODING`.
3. `THIRD_PARTY_CHILD_NETWORK_FAIL_CLOSED`: the child fails closed when the sanitized environment cannot resolve the public host.
4. `THIRD_PARTY_NO_HIDDEN_AUTHORITY`: no ambient proxy, credential inheritance, hidden retry, shell execution, bridge execution, or consumer execution is introduced.
5. `GENERIC_DYNAMIC_OUTPUT_NO_GUESSED_SEMANTICS`: static Auto Connect refuses to invent field mappings for a dynamic HTTP response.
6. `NATIVE_TRANSPORT_GLOBAL_PROXY_BOUNDARY`: the default native path completes the bounded read while Node's standard global proxy API points at an unavailable loopback endpoint.
7. `CURL_NATIVE_DIFFERENTIAL_ROOT`: an independent curl/libcurl replay matches the declared selected-field root while intentionally not equating unprojected wire roots.
8. `AUTHORITY_ZERO`: all receipts remain evidence-only; no agreement, protocol, or canonical authority is promoted.

## Lowering / provider evidence

- OPP protocol and bridge semantics remain the canonical OPP owner.
- Python child invocation is an auxiliary host lowering with explicit consent, path containment, sanitized environment, timeout, output limits, and fail-closed errors.
- TINP is an inspected transport donor/owner, not a copied implementation and not an OPP protocol owner.
- The public GitHub response is host-level evidence only; the OPP child result is negative evidence, not a third-party PASS.

## K400 nine-gate delta

| Gate | Candidate evidence posture | Ruling |
|---|---|---|
| `EXPRESS` | OPP protocol, bridge and run-spec declarations exist | Candidate input only |
| `COMPILE` | Source compile and schema/test compilation pass locally | Candidate input only |
| `LOWER` | Python host lowering and TINP adapter archaeology are bounded | Candidate input only |
| `EXECUTE` | Local fixture PASS; external child attempt FAIL_CLOSED | Candidate input only |
| `CORRECT` | Positive fixture plus negative network/semantic cases | Candidate input only |
| `ROBUST` | Bounded timeout/output/path/locale and no-hidden-retry checks | Candidate input only |
| `PERFORMANCE` | No production or cross-host performance run | `NOT_RUN` |
| `AI_GENERATE` | No independent generation evaluation | `NOT_CLAIMED` |
| `EVIDENCE` | Content-rooted receipts and Court ledgers exist | Candidate input only |

The nine gates are non-compensatory. No K400 PASS, RCL Core absorption, or authority transfer is granted.

## Next frontier

Review the existing TINP↔OPP adapter version, native network/proxy policy and receipt contract, then obtain a separately owned provider/producer with its own receipt and authority boundary. The curl replay is only differential runtime evidence; the correct status remains candidate-only / `NOT_VERIFIED`.
