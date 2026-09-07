# TaoWind OPP — Open Reality Protocols（道风开放现实协议族）

> **OPP = Open Reality Protocols（开放现实协议族）**。本仓库把 TaoWind / RCL / RNCS / DWAC 中已经出现的协议、契约、接口、模式、能力、证据、回执、账本与桥接原语，收束成一套可读、可验证、可协商的开放协议候选。

当前版本：`0.1.0-candidate.1`（候选版 1）。当前状态：**CANDIDATE（候选）**，不是互联网标准、生产安全标准或外部权威认证标准。

## 第一批 6 个核心协议

| 缩写 | 英文名 | 中文名 | 机器协议 ID | 作用 |
|---|---|---|---|---|
| RXP | Reality Exchange Protocol | 现实交换协议 | `opp.rxp.v0.1` | 统一 Reality Envelope（现实信封），负责跨系统承载事实、状态、意图、能力、约束、证据与动作描述。 |
| RCP | Reality Capability Protocol | 现实能力协议 | `opp.rcp.v0.1` | 描述实体会什么、输入输出、权限、成本、确定性、副作用和证据。 |
| RAP | Reality Artifact Protocol | 现实工件协议 | `opp.rap.v0.1` | 描述代码、文档、模型、世界、数据库等任意工件的目标、依赖、来源、验证与生命周期。 |
| REP | Reality Evidence Protocol | 现实证据协议 | `opp.rep.v0.1` | 让 Claim（主张）绑定 Source（来源）、Method（方法）、Confidence（置信度）、Negative Evidence（负证据）和可复现信息。 |
| RSP | Reality State Protocol | 现实状态协议 | `opp.rsp.v0.1` | 交换对象、关系、事实、观察、预测、假设、分支与状态根，强制区分“事实”和“预测”。 |
| CHP | Civilization Handshake Protocol | 文明握手协议 | `opp.chp.v0.1` | 两个陌生系统先协商协议、能力、权限与证据政策，再建立会话。 |

## 9 类标准原语

OPP 明确区分以下九种东西，避免把所有东西都叫 API（应用程序接口）：

1. `protocol` — Protocol（协议）：规定双方如何互动。
2. `contract` — Contract（契约）：规定参与方必须满足的条件。
3. `interface` — Interface（接口）：规定如何调用能力。
4. `schema` — Schema（模式）：规定数据结构。
5. `capability` — Capability（能力）：规定实体能做什么。
6. `evidence` — Evidence（证据）：规定为什么相信一个结果。
7. `receipt` — Receipt（回执）：证明某次动作或验证实际发生。
8. `ledger` — Ledger（账本）：保存按时间组织的事实、动作或证据历史。
9. `bridge` — Bridge（桥）：在不同协议、运行时或语义体系之间做受约束的转换。

## 可执行部分

仓库不只放规范文档，还提供：

- Draft 2020-12 JSON Schema（JSON 模式）验证；
- 协议注册表；
- SHA-256 canonical content root（规范化内容根）完整性封装；
- CHP 文明握手的确定性协商运行时；
- Python CLI（命令行接口）；
- RCL（Reality Compiler Language，现实编译语言）语义桥候选；
- 示例包与单元测试；
- DWAC 协作编译证据与资产考古映射。

## 本地使用

```bash
python -m pip install -e .
python -m opp validate examples/capability.json
python -m opp validate examples/artifact.json
python -m unittest discover -s tests -v
```

`python -m opp validate ...` 的中文意思是“用 OPP 验证器检查一个现实信封及其协议负载”。

## 权威边界

- OPP 当前只证明：本仓库中的模式、验证器、完整性根、协商逻辑和测试在本地候选环境中可工作。
- Schema PASS（模式通过）不等于事实为真；它只说明结构与声明边界符合规范。
- SHA-256 根证明内容一致性，不自动证明签名者身份、法律权威、外部时间戳或现实真实性。
- Handshake PASS（握手通过）只表示双方存在可协商交集，不代表任何一方自动获得新权限。
- 所有跨系统 Canonical（规范所有权）提升、世界事实提升、权威委托必须由上层治理系统另行批准。

更多内容见 `docs/SPECIFICATION.md`、`docs/PRIMITIVES.md`、`docs/ARCHAEOLOGY.md` 与 `docs/GOVERNANCE.md`。


## Bridge Compiler（桥编译器）

OPP v0.1 现包含静态 Bridge Compiler，可扫描任意代码/文档仓库中的协议性原语，并生成 REP/RAP/RCP/CHP 候选桥接包。详见 `docs/BRIDGE_COMPILER.md`。

```bash
opp bridge scan ./repo --profile auto
opp bridge compile ./repo --out ./bridge-output
```
