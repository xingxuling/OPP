# OPP roadmap

## Completed in the external-onboarding candidate

- Public `opp.sdk` surface backed by existing OPP implementations; legacy imports retained.
- Windows UTF-8 repair reused from the previous candidate branch.
- Unknown type comparison stays unknown; bridge plan root checked before execution.
- Offline, original-input-bound success receipt verification through SDK and CLI.
- Three real installed libraries, positive/negative/recovery runs and cross-language receipt checks.
- Installable wheel tested outside the source tree; repeatable evidence script and package provenance.

## Next smallest gaps

1. Improve discovery from existing type stubs and explicit external JSON contracts before adding another IR.
2. Run a real independently maintained MCP server with the official client and preserve negotiation failures.
3. Stabilize public SDK regression contracts over multiple releases and recruit an independent consumer.
4. Join a real external capability to TINP's authorized routing/failover path, without moving OPP ownership.

## External gates

An independently operated consumer/security review has not run. TINP authority,
physical devices, trusted time and key custody cannot be substituted by OPP hashes.
Local measurements are not production performance or availability commitments.
