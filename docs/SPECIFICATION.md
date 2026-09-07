# OPP v0.1 Specification（OPP v0.1 规范）

## 1. 目标

OPP 的核心不是再造一种网络传输，而是定义**跨系统可以交换的语义单位**。HTTP（超文本传输协议）、WebSocket（网页双向通信协议）、文件、消息队列、函数调用或本地进程都可以作为底层 Transport（传输层）；OPP 负责上层“交换什么、如何声明边界、如何验证结构、如何协商能力”。

## 2. Reality Envelope（现实信封）

所有 OPP 消息使用统一 Reality Envelope。核心字段：

- `format`：信封格式。
- `protocol`：实际负载采用的协议 ID。
- `version`：发出端实现版本。
- `kind`：九类标准原语之一。
- `id`：本消息/工件/状态的稳定标识。
- `status`：`candidate / experimental / stable / deprecated / rejected`（候选 / 实验 / 稳定 / 已弃用 / 已拒绝）。
- `issuer`：发布实体；这里只是声明，不等价于密码学认证。
- `payload`：协议负载。
- `constraints`：必须保留的约束。
- `evidenceRefs`：证据引用。
- `integrity`：可选 SHA-256 内容根。

## 3. RXP — Reality Exchange Protocol（现实交换协议）

RXP 是 OPP 的统一交换信封语义。它允许负载声明 `semanticClass`（语义类别）与 `content`（内容），并可附带 `intent`（意图）、`actions`（动作候选）与 `rollback`（回滚描述）。

RXP **不执行动作**。执行权属于宿主运行时；RXP 只描述可交换的语义与约束。

## 4. RCP — Reality Capability Protocol（现实能力协议）

RCP 最低要求：

- `capabilityId`：能力 ID；
- `domain`：能力域；
- `operation`：动作；
- `inputModalities / outputModalities`：输入/输出模态；
- `determinism`：确定性等级；
- `statefulness`：状态性；
- `authorityRequired`：所需权限；
- `sideEffects`：副作用；
- `reversibility`：可逆性；
- `evidence`：支持能力声明的证据引用。

能力声明默认不产生权限，也不自动意味着当前可用。

## 5. RAP — Reality Artifact Protocol（现实工件协议）

RAP 把“工件”定义为任何可识别、可版本化、可验证的产物。包括但不限于代码、文档、图片、模型、数据集、数据库、世界状态、游戏、服务、PRD（产品需求文档）与复合项目。

核心结构：身份 → 类型 → 目标 → 依赖 → 来源 → 约束 → 验收 → 生命周期 → 可执行语义。

## 6. REP — Reality Evidence Protocol（现实证据协议）

REP 不把“有引用”当成“有证据”。每个 evidence bundle（证据包）至少包含：

- claim（主张）；
- source（来源）；
- method（方法）；
- confidence（置信度）；
- independence（独立性）；
- negativeEvidence（负证据）；
- reproduction（复现路径）；
- boundary（结论边界）。

## 7. RSP — Reality State Protocol（现实状态协议）

RSP 规定状态交换必须区分：

- `observed`（观察事实候选）；
- `derived`（推导状态）；
- `predicted`（预测）；
- `hypothetical`（假设）；
- `declared`（主体/系统声明）；
- `simulated`（模拟状态）。

预测不得静默提升成观察事实。状态更新用 `baseRoot`、`revision`、`stateRoot` 提供可追踪的版本链。

## 8. CHP — Civilization Handshake Protocol（文明握手协议）

CHP 的最小流程：

1. Identity Offer（身份提议）；
2. Protocol Discovery（协议发现）；
3. Capability Discovery（能力发现）；
4. Evidence Policy Exchange（证据政策交换）；
5. Authority Scope Intersection（权限范围求交）；
6. Agreement / Reject（达成协议 / 拒绝）。

本仓库的参考协商器只做集合交集和明确规则检查，不自动创建权限、不自动调用远端工具、不自动执行外部动作。

## 9. 版本兼容

- `v0.x`：Candidate/Experimental（候选/实验）阶段，允许不兼容调整，但必须修改协议 ID 或版本并留下迁移说明。
- 同一协议 ID 的实现应按注册表 `compatibility` 字段决定兼容策略。
- 未知扩展必须放入 `extensions`，核心验证器默认保留但不解释。

## 10. 安全与证据边界

OPP 是语义协议层，不是认证、加密、网络沙箱或法律授权系统。生产部署必须叠加实际身份认证、传输加密、权限控制、审计与密钥管理。
