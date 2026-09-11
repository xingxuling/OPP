# Integration Court — Third-party Network Boundary

## Current Reality

- Repository: `xingxuling/OPP`
- Starting candidate: `22ff5830c8c080bf2e5f8ed58073119445aeecad`
- Candidate branch: `codex/opp-third-party-boundary-v01`
- External system: public GitHub REST `GET /repos/xingxuling/OPP`
- Host preflight: HTTP `200`; selected fields were `full_name`, `default_branch`, and `private`.
- Static OPP audit scanned 5 files and found 2 callable interfaces; Auto Connect compared 0 pairs and accepted 0 because the dynamic HTTP response stayed a generic object.
- OPP child attempt: explicit consent was supplied, but the producer failed closed with `GITHUB_NETWORK_ERROR:gaierror` before the bridge or consumer ran.
- Donor archaeology: TINP `codex/next-internet-v01@1aa235d9f5718f87c959e275da10a7bf12d58e9f` owns reusable UDP/TCP/TLS loopback transport and an OPP negotiation adapter, but does not provide public HTTP/REST or cross-host production network evidence.

## What Changed

- Added a manual read-only third-party fixture under `examples/third-party-fixtures/`.
- Added a candidate interop run spec with an exact declarative identity bridge.
- Recorded both the host-level external observation and the OPP child negative receipt.
- No OPP Core protocol, RCL semantic owner, or authority boundary was changed.

## Evidence

- Machine evidence: `evidence/OPP_THIRD_PARTY_BOUNDARY_2026-09-11.json`
- RCL stress ledger: `docs/RCL_STRESS_FIELD_2026-09-11.md`
- Evidence root: `dec1dbf2e2dd8ee5b9129bbfe4039b7c945abec2920e4b122934eeb72cc4aa58`
- Host selected response root: `a97a84ea4b0b782a102fd59c7cae8e03368271e0430a77da848553cbfe131130`
- Failed OPP interop receipt root: `c4be98a06bd59dc35ad1aedef028368a3e13b675100fd806373b16975b07d911`
- Failed producer receipt root: `a5d3fee7b21a9d83f4462e61d1e958df264b2cb4f2fb5742104c4727b61e7280`

## Tests

- Parent host read-only GitHub REST preflight: `PASS`, HTTP `200`.
- OPP `interop run --allow-execution`: `FAIL_CLOSED`, `PRODUCER_FAILED`.
- OPP static Auto Connect: `0` accepted plans; no field semantics were guessed.
- Bridge and consumer were not executed after producer failure.
- No hidden retry or proxy/credential inheritance occurred.

## Claims Promoted

- A reproducible negative cross-process evidence case now exists for third-party network access under OPP's sanitized child policy.

This does not promote third-party interoperability, HTTP adapter support, or production status.

## Claims Still Forbidden

- No `THIRD_PARTY_VERIFIED` interoperability claim.
- No claim that OPP is a general HTTP/OpenAPI/MCP adapter.
- No claim of network reachability from a bounded child process.
- No claim of cross-host or production readiness.

## Remaining Production Gaps

`OPP-TRANSPORT-001` is open: TINP or a mature external HTTP adapter must own the declared proxy/network policy and receipts. OPP must consume that adapter without copying the transport stack, and the child must not silently inherit ambient network authority.

## Next Frontier

Resolve the TINP↔OPP adapter version/policy binding first. Re-run the same public GET only after an explicit transport owner, proxy policy and receipt contract exist.

## Merge / Release Decision

The fixture and negative evidence are candidate-only and may be reviewed independently. Do not merge them as proof of third-party interoperability; the network boundary remains open. The RCL stress ledger records candidate input only and grants no K400 or RCL Core promotion.
