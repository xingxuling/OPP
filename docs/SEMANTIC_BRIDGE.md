# OPP Semantic Bridge v0.2（OPP 语义桥 v0.2）

## 目标

Bridge Compiler v0.1 解决“项目声明了哪些 Protocol / Contract / Schema / Capability（协议 / 契约 / 模式 / 能力）”。v0.2 增加第二层：**这个接口静态上接收什么、输出什么、可能有什么副作用，以及它与另一个接口能否安全连接。**

## Semantic Interface IR（语义接口中间表示）

每个接口至少包含：

- `interfaceId`：稳定候选标识；
- `interfaceKind`：`callable / schema / endpoint / unknown`（可调用项 / 模式 / 端点 / 未知）；
- `inputs / outputs`：输入与输出端口；
- `shape`：JSON-Schema-like（类 JSON 模式）的有界数据形状；
- `sideEffects`：静态可见副作用候选；
- `authorityRequired`：明确声明的权限需求；当前静态提取器不会凭空推断权限；
- `confidence`：推断置信度；
- `runtimeSupport`：默认 `unverified`（未验证）。

当前静态提取：

1. Python AST（Python 抽象语法树）：函数参数/返回类型注解、默认值，以及有界副作用调用；
2. JavaScript / TypeScript（JavaScript / 类型脚本）：函数与箭头函数签名；TypeScript 类型可降低为有限数据形状；
3. JSON Schema（JSON 模式）：把模式本身视为高置信数据接口。

任何被扫描源码都不会被 `import`、执行或动态求值。

## Compatibility Class（兼容等级）

- `exact`（精确）：形状相同；
- `structural`（结构兼容）：可通过安全结构变换连接，例如规范化字段名重命名、integer→number（整数→数值）；
- `lossy`（有损）：必须丢弃源数据才能满足目标，例如目标禁止额外字段；默认拒绝自动生成，必须显式 `allow_lossy`；
- `incompatible`（不兼容）：缺少必需信息、类型冲突或权限存在缺口；
- `unknown`（未知）：静态证据不足，不猜。

类型兼容与语义兼容是两个不同问题。即使结构可转换，如果语义标签明确冲突，也会降为 `unknown`。

## Declarative Transform Runtime（声明式转换运行时）

当前只允许 OPP 自有、可审计的操作：

- `identity`（恒等）；
- `rename`（字段重命名）；
- `select`（字段投影）；
- `inject-default`（注入已声明默认值）。

运行时拒绝任意代码操作，例如 `python`、`shell`、动态表达式。它只变换 JSON-like（类 JSON）值。

## Authority / Information Boundary（权限 / 信息边界）

自动桥不得：

- 创造目标要求但源端没有提供的必需信息；
- 创造源端没有的权限；
- 把静态发现升级成运行时可用；
- 把候选桥升级成生产权威；
- 因为“类型能对上”就宣称业务语义正确。

## RCP Projection（RCP 能力投影）

静态语义接口会被投影成 `opp.rcp.v0.1` 的 candidate-only（仅候选）能力描述，并绑定 REP（现实证据协议）证据。`inputSchema / outputSchema` 来自静态签名或模式；`availability` 固定为 `candidate-only`，`sourceAuthorityInherited=false`。
