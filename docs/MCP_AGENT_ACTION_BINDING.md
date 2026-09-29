# MCP → OPP Agent Action Binding v0.1

这层把 MCP `tools/list` 返回的一项工具声明，绑定到 OPP 的 RCP capability（能力声明）和 Agent Action Contract（智能体行动契约）。

```text
MCP tools/list
   ↓ raw tool root
OPP RCP declaration
   ↓
OPP Agent Action Contract
   ↓
TINP / RCL enforcement
```

关键原则：**MCP annotations（工具注解）只当提示，不当权限。**

即使工具写了 `readOnlyHint=true`，OPP 也不会据此自动授予 `workspace.read`，更不会取消文件资源绑定。真正进入 Action Contract 的 `authorityRequired`、`sideEffects`、`reversibility` 和 `resources` 必须显式提供并被 root 绑定。

Binding 同时绑定：

- 原始 MCP tool descriptor 的 `mcpToolRoot`
- OPP RCP declaration 的 `capabilityRoot`
- Agent Action Contract 的 `actionContractRoot`
- 总 `bindingRoot`

这样 MCP server 更新 schema、工具名或 descriptor 后，旧 binding 不会静默继续使用。

当前仍不证明 MCP server 诚实报告了真实副作用，也不替代 TINP 的身份/Authority Lease（权限租约）或实际执行边界。
