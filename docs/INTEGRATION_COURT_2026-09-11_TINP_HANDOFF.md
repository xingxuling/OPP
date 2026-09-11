# Integration Court — TINP policy-bound HTTP handoff

## Current Reality

- OPP consumer branch: `codex/opp-third-party-boundary-v01@66efb18` (handoff verifier source at `97b770b`).
- TINP provider candidate: `codex/tinp-transport-policy-v01@6314cb0f84be725a388996119783be5e3c4fa2bb`.
- TINP policy format: `twni.opp-http-readonly-policy.v1`.
- TINP receipt format: `twni.opp-http-readonly-receipt.v1`.
- Public GitHub REST request: explicit HTTPS `GET`, exact host/path allowlist, no credentials, no redirect, one attempt; host response was HTTP `200`.
- OPP direct sanitized child network attempt remains `FAIL_CLOSED`; this handoff does not weaken that boundary.

## What Changed

- TINP added a transport-owned read-only HTTP policy and bounded JSON adapter with explicit response-field projection, wire/projected roots, timeout and response-size limits, ambient-proxy denial, credential denial and no retry.
- OPP added a handoff verifier that checks the TINP receipt root, policy/request binding, projected response root and evidence-only boundary before invoking the existing bounded local consumer.
- No OPP Core protocol, RCL semantic owner, authority lease or production credential was added.

## Evidence

- TINP live run: [OPP_HTTP_READONLY_GITHUB_2026-09-11.json](C:/Users/User/Documents/RCL/_worktrees/tinp-transport-policy-v01/evidence/OPP_HTTP_READONLY_GITHUB_2026-09-11.json)
- TINP hardening evidence: [OPP_HTTP_READONLY_HARDENING_2026-09-11.json](C:/Users/User/Documents/RCL/_worktrees/tinp-transport-policy-v01/evidence/OPP_HTTP_READONLY_HARDENING_2026-09-11.json)
- OPP handoff evidence: [OPP_TINP_HTTP_HANDOFF_2026-09-11.json](C:/Users/User/Documents/RCL/_worktrees/opp-production-audit-v01/evidence/OPP_TINP_HTTP_HANDOFF_2026-09-11.json)
- OPP independent handoff-boundary evidence: [OPP_TINP_HANDOFF_HARDENING_2026-09-11.json](C:/Users/User/Documents/RCL/_worktrees/opp-production-audit-v01/evidence/OPP_TINP_HANDOFF_HARDENING_2026-09-11.json)
- TINP policy root: `0b0626c2784f40ab7afade7f69f9f7374710cc6fac621accd1089bac32cedc0d`
- TINP provider receipt root: `678062d0333113b7c3f3bba66ae3e93aeebdbf65bf401812d85f210c546dcf41`
- Projected response root: `a97a84ea4b0b782a102fd59c7cae8e03368271e0430a77da848553cbfe131130`
- OPP handoff root: `a23df78c116d5fb3ef9d9e420fa2357cf617303e688c755a8397caf4a67ddcb5`
- OPP consumer receipt root: `169ce0158098e5c61500b221d0bc65088ed6484948b705d310d2255f18c6eece`

## Tests

- TINP adapter tests: `8/8 PASS`; full suite: `182/182 PASS`.
- OPP source-tree suite: `46/46 PASS` (`43` baseline tests plus `3` handoff-boundary tests).
- OPP handoff verifier and bounded consumer: `PASS`.
- Provider response root equals the OPP canonical root of the projected fields.
- No retry, redirect, ambient proxy, credential inheritance or authority promotion occurred.

## Claims Promoted

- One concrete TINP policy-bound external observation can be handed to one explicit OPP consumer with both provider and consumer receipts bound by roots.
- The response projection is declared, not inferred by Auto Connect.

This remains a candidate handoff claim, not a universal or independent third-party interoperability claim.

## Claims Still Forbidden

- No `THIRD_PARTY_VERIFIED` universal interoperability claim.
- No general HTTP/OpenAPI/MCP adapter claim for OPP.
- No direct network reachability claim for the OPP sanitized child.
- No cross-host, production, proxy-support, credential-custody, SLA or authority claim.
- No RCL Core or K400 promotion.

## Remaining Production Gaps

`OPP-TRANSPORT-001` now has a concrete TINP candidate contract, but it is not merged, independently reviewed or production-ready. Physical cross-host transport, external certificate/credential lifecycle, proxy policy, failure recovery and independent external producer behavior remain open.

`OPP-THIRD-PARTY-001` remains below independent third-party verification: GitHub supplied the observed data, but the executable provider is a TaoWind TINP candidate and the OPP consumer is an explicit local fixture.

## Next Frontier

Integration Court review of the TINP candidate, followed by a second genuinely independent producer/consumer or a separately owned transport provider. Preserve the current exact policy and receipt roots so the experiment can be repeated without broadening authority.

## Merge / Release Decision

The TINP and OPP branches are pushed candidate work only. Do not merge them as production network capability or label OPP generally third-party interoperable.
