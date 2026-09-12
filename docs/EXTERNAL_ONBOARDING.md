# External onboarding experiment — 2026-09-12

Status: **real third-party libraries executed by our local operator**. This is not
independently operated third-party acceptance. No fixtures substitute for the
third-party implementations: the manually written adapters import installed
Boltons, more-itertools and JMESPath distributions in OPP's real Python children.

The current audit began at OPP `5b18ca5b1df88791f69175811a1bb0912cf5d0bb`.
Existing UTF-8 fixes from `22ff583` were reused. No new protocol was introduced.

| External project | Installed version | Discovered top-level interfaces / unknown outputs | Real chain | Failure / recovery |
| --- | --- | --- | --- | --- |
| [Boltons](https://github.com/mahmoud/boltons) | 26.2.0 | 175 / 173 | unique → OPP field rename → more-itertools chunked | integer input raises TypeError; explicit valid invocation succeeds |
| [more-itertools](https://github.com/more-itertools/more-itertools) | 11.1.0 | 180 / 180 | unique_everseen → rename → JMESPath sort | integer input raises TypeError; explicit valid invocation succeeds |
| [JMESPath](https://github.com/jmespath/jmespath.py) | 1.1.0 | 32 / 32 | sort → rename → Boltons unique | invalid input raises JMESPathTypeError; explicit valid invocation succeeds |

The OPP bridge automatically synthesized `item_list → itemList` from manually
declared JSON shapes. Library selection, API selection, wrappers, contracts and
dependency installation were manual. The original library signatures alone did
not prove these executable bridges. Unknown-to-unknown shape comparison now remains
UNKNOWN rather than incorrectly becoming EXACT.

The [initial machine summary](../evidence/external-onboarding-2026-09-12/summary.json)
records 2.5374 / 2.3773 / 1.8956 seconds for success, negative case, recovery and
offline checks, plus separate scan times. These are automated execution timings,
not a novice's integration time. Manual authoring and installation time was not
measured and is explicitly null. The [final wheel replay](../evidence/external-onboarding-2026-09-12/final-wheel-replay/summary.json)
retains a fresh run of the final implementation.

Both Python input-bound verification and the separate TINP JavaScript receipt
implementation accepted these outputs. TINP's `scripts/external-verify.mjs` records
zero network requests and target executions. The JavaScript check validates receipt
consistency; the OPP check additionally binds the caller-retained spec and input.
Both were run by the same operator, so neither is an independent attestation.

The companion TINP experiment adds two independently maintained remote projects:
Open-Meteo completed HTTPS 200 → invalid-latitude 400 → corrected 200 with offline
receipts. go-httpbin's httpbingo endpoint returned HTTP 402 for all three requests;
its recovery is **not verified**, and the reason behind the 402 is unknown.
This gives five external projects attempted, four with bounded positive runtime
evidence. The remote services themselves did not negotiate OPP or speak TINP.

## Remaining external gates

General Provider SDK registration, live MCP interop, multi-hop execution of these
libraries, failover with the same authorized external capability, physical devices,
real authority/key lifecycle/trusted time and an independent operator remain open.
The result is useful onboarding evidence, not the completed OPP + TINP joint chain.

## License and source evidence

OPP current upstream includes MIT LICENSE. The installed Boltons distribution has
BSD licensing, more-itertools MIT and JMESPath MIT; exact distribution metadata and
license-file hashes are archived in each `*-source.json`. No library source is
vendored into OPP. Experiments run installed packages from pinned requirements.
Repository HEAD clones were inspected only as context; installed distribution
hashes identify the code that actually ran, avoiding a false HEAD/package match.

RCL ownership and nine-gate treatment are recorded in `RCL_STRESS.json` in the
evidence directory. No RCL Core change or K400 promotion is claimed.

Final code replay: [34692507409](https://github.com/xingxuling/TINP/actions/runs/34692507409), all three hosted jobs PASS; OPP `7c4970c`, TINP `692c0e4`. The earlier run is retained as historical evidence.
