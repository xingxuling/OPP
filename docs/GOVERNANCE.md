# OPP Governance（OPP 治理）

## 状态等级

- `experimental`（实验）：结构可能快速变化，只适合探索。
- `candidate`（候选）：已有模式、实现与测试，但未承诺稳定兼容。
- `stable`（稳定）：需要明确版本政策、兼容测试和实现证据后才能提升。
- `deprecated`（已弃用）：保留兼容期但不建议新接入。
- `rejected`（已拒绝）：明确记录失败或不采纳原因。

## Promotion gate（提升闸门）

从 candidate（候选）提升到 stable（稳定）至少需要：

1. 规范冻结；
2. JSON Schema（JSON 模式）通过；
3. 两个独立实现或一个实现 + 一个独立兼容测试器；
4. 正向与负向互操作测试；
5. 安全边界文档；
6. 版本迁移策略；
7. Evidence Receipt（证据回执）；
8. 无静默 Authority Promotion（权限提升）。

## Extension（扩展）

扩展必须命名空间化，例如 `taowind.dwac.*`、`taowind.rncs.*`。未知扩展默认“保留但不执行”。

## Registry（注册表）

`registry/protocols.json` 是候选协议发现入口，但它不是中心化权威根。未来可以增加签名注册表、联邦注册表和镜像机制。
