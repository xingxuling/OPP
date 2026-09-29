# OPP Agent Action Profile v0.1

`opp.agent-action.v0.1` is a bounded semantic profile for proposed Agent actions.
It answers **what action is being proposed, what resource it targets, what side
effect/reversibility is declared, and whether a provider claims semantic support**.

It deliberately does **not** answer whether the caller is trusted or authorized.
`authorityGranted` remains `false` in every OPP artifact. A separate authority
owner such as TINP must verify subject/session/lease/revocation and enforce the
result at the execution boundary.

## First vertical

The initial Code-Agent security vocabulary is intentionally small:

- `filesystem.read` / `filesystem.write`
- `credential.read`
- `network.egress`
- `process.spawn`
- `package.inspect` / `package.install`
- `git.remote.write`

The profile does not execute any operation. Provider declarations use exact
resource scopes or explicit lexical-prefix scopes ending in `*`. Network hosts
are separately declared so a generic URL/resource match cannot silently become
credential-exfiltration authority.

## Flow

```text
Agent / untrusted prompt content
        ↓ proposed action
OPP Agent Action Profile
        ↓ semantic contract, authorityGranted=false
TINP lease + RCL admission
        ↓ allow / deny
Host sandbox / provider
        ↓ execution receipt
TINP evidence / recovery
```

A `DIRECT` result means only that explicit provider declarations cover the
requested action surface. It does not prove provider honesty, path/symlink safety,
network identity, sandbox strength, exactly-once side effects, or production
authorization.
