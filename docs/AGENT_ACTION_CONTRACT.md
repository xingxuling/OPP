# Agent Action Contract v0.1

## 目的

这一 profile（配置档）把 OPP 从“接口能不能接”推进到“这次 Agent 行动可能产生什么副作用”。

它仍然属于 OPP 的**语义互操作层**，不接管身份、授权、密钥、沙箱或最终执行。权限执行仍交给 TINP / 宿主安全边界。

```text
Agent / MCP / API
      ↓
RCP capability
      ↓
OPP Agent Action Contract
      ↓
requiredAuthority
declaredEffects
acceptedEffects
resources
reversibility
contractRoot
      ↓
TINP enforcement
```

## 核心不变量

1. **能力声明不等于权限。** `authorityGranted` 永远是 `false`。
2. **安全效果必须完整确认。** Provider 声明的全部 `sideEffects`，以及 `workspace.read` 等已知显式权限所对应的资源访问效果，都必须由调用方显式接受。
3. **未知副作用不猜。** 未进入已知 effect vocabulary（副作用词表）的值进入 `negotiate`。
4. **高风险副作用必须绑定资源。** 文件、网络、命令、包安装等不能只写“允许”，还要说明作用对象。
5. **root 绑定能力和行动。** TINP 可以跨语言复算 SHA-256 canonical JSON root（规范 JSON 内容根）。
6. **OPP 不声称运行时真实遵守声明。** 执行后的事实仍要由 TINP / sandbox / evidence（证据）核验。

## v0.1 已知 effect vocabulary

- `filesystem.read`
- `filesystem.write`
- `credential.read`
- `credential.write`
- `network.egress`
- `process.spawn`
- `package.install`
- `package.script`
- `registry.publish`
- `git.write`

兼容别名包括 `workspace.read → filesystem.read`、`workspace.write → filesystem.write`、`npm.postinstall → package.script` 等。这里不是自由推断：只有固定词表中的显式 scope（权限范围）才会被提升为安全效果，其他自定义 scope 仍只作为权限要求保留。

## 资源绑定

`resources` 固定为四类：

```json
{
  "filesystem": ["workspace/project"],
  "network": ["registry.npmjs.org"],
  "commands": ["npm test"],
  "packages": ["example@1.2.3"]
}
```

v0.1 不做通配符推理，也不自动把 URL、shell 或任意字符串提升成权限。

## 面向 prompt injection（提示注入）的意义

如果一个 Code Agent 原本只有：

```text
filesystem.read: workspace/project
```

而被恶意 README / issue / tool output 诱导去请求：

```text
credential.read: ~/.ssh/id_rsa
network.egress: attacker.example
process.spawn: powershell ...
```

OPP 的职责不是判断“这段文字是不是攻击”，而是把这些行为压成显式 Action Contract。TINP 再根据真实 Authority Lease（权限租约）做 fail-closed（失败关闭）准入。

这使安全边界依赖**行动权限**，而不是必须提前认识每一种攻击文本。
