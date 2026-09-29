# OPP Agent Action Profile v0.1

This candidate profile turns an explicit Code Agent / MCP tool action into a small deterministic authority/effect contract. It is intentionally descriptive: **OPP does not grant authority and does not execute the action**.

## Flow

```text
Tool / Agent request
  -> explicit operations
  -> OPP agent-action profile
  -> authorities + side effects + targets + reversibility + contractRoot
  -> TINP (or another control plane) evaluates authenticated authority
```

Supported operation vocabulary in v0.1:

- `filesystem.read` -> `workspace.read`
- `filesystem.write` -> `workspace.write`
- `shell.exec` -> `process.spawn`
- `network.egress` -> `network.egress`
- `credential.read` -> `credential.read`
- `package.install` -> `package.install + workspace.write + network.egress`
- `package.lifecycle-script` -> `process.spawn`
- `scm.write` -> `scm.write + network.egress`

Unknown operations fail closed. The compiler does not infer authority from free-form prompt text.

## Example: npm install with lifecycle scripts

The resulting contract must expose `process.spawn` instead of hiding it behind a generic package-install label. A TINP lease that allows package installation and registry egress but does not allow process spawning can therefore reject the action before execution.

## Security boundary

This profile is not a sandbox, antivirus, authentication system, or authority owner. It only produces a rooted semantic contract. Production use still requires authenticated identity, transport security, execution isolation, key management, and a non-bypassable enforcement point.
