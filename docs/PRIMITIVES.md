# OPP Primitive Model（OPP 原语模型）

## 九类原语不是同义词

| 原语 | 中文解释 | 典型问题 |
|---|---|---|
| Protocol（协议） | 交互规则 | “双方按什么步骤说话？” |
| Contract（契约） | 条件与责任 | “你必须满足什么才可参与？” |
| Interface（接口） | 调用面 | “我怎么调用你？” |
| Schema（模式） | 数据形状 | “数据长什么样？” |
| Capability（能力） | 可做事项 | “你会什么？” |
| Evidence（证据） | 相信依据 | “凭什么相信？” |
| Receipt（回执） | 已发生证明 | “这次动作真的执行了吗？” |
| Ledger（账本） | 历史序列 | “过去发生过什么？” |
| Bridge（桥） | 受约束转换 | “两个体系如何翻译？” |

## 组合原则

一个完整的跨文明操作通常不是一个 API，而是：

`Handshake（握手） → Capability（能力） → Contract（契约） → Interface（接口） → Protocol（协议） → Receipt（回执） → Evidence（证据） → Ledger（账本）`

如果两侧 Schema（模式）不同，则在中间插入 Bridge（桥）。

## Authority rule（权限规则）

任何协议对象都不得因为“被序列化、被接收、被验证或被桥接”而自动获得更高 Authority（权限/权威）。这条规则来自 RCL / DWAC 已有的 candidate-only（仅候选）和 no-silent-promotion（禁止静默提升）设计。
