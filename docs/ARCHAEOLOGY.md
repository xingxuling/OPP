# Asset Archaeology（资产考古）

OPP v0.1 不是从空白发明。以下结构在既有 TaoWind 项目中已经存在，本仓库只做跨项目抽象和标准化。

## RCL（Reality Compiler Language，现实编译语言）

本轮 GitHub 考古观察到 RCL `main` 代码快照 `a7d6f7b0844323df50c91fd807ad3ee76e24f90d` 附近存在：

- `foundation-contract.mjs`：Foundation Contract（基础契约）；
- `relational-transaction-protocol.mjs`：Relational Transaction Protocol（关系事务协议），包含 schema / snapshot / query / transaction / commit / provider receipt / recovery；
- `rncs-execution-bridge-v2.mjs`：RNCS Provider Contract（RNCS 提供者契约）与执行桥；
- `llm-like-runtime.mjs`：LLM Provider Contract（大语言模型提供者契约）；
- `frontier-external-observation-contract.mjs`：External Observation Contract（外部观测契约）；
- `real-world-data-ingestion-layer.mjs`：Real World Data Source Contract（现实世界数据源契约）；
- `profiler-debug-ui-runtime.mjs`：Debug UI Protocol（调试界面协议）；
- `experiment-design-synthesizer.mjs`：Experiment Protocol（实验协议）；
- `ial-civilization-product-os.mjs`：Qinglian Communication Gatekeeper Protocol（青莲通信门控协议）和 Wind Product Interface System（风系产品接口系统）。

## RNCS（Reality Neural Computing System，现实神经计算系统）

RNCS 的 Reality Computation Language（现实计算语言）文档已出现 capability-safe provider runtime（能力安全提供者运行时）、resource isolation kernel（资源隔离内核）与 RNCS execution bridge（RNCS 执行桥）路线。这给 OPP 的 Provider / Capability / Bridge 三类原语提供了已有运行时背景。

## DWAC（Distributed Whole-Artifact Compiler，分布式全工件编译器）

本轮用户提供的 DWAC ZIP：

- SHA-256：`8d77f42f58cb10c01c1cd7945f84864d5f852e4a48b6a31dfb8b346899ae3888`
- 核心协议/契约：`WORKER_PROTOCOL_v1.json`、`DWAC_USCE_FEDERATION_CONTRACT_v4.json`、`API_CONTRACT_v1_4.json`、`organs/WORKER_FEDERATION_CONTRACT_v0.3.json`、`organs/COGNITIVE_PROVIDER_CONTRACT_v0.1.json`；
- 能力模式：`organs/UNIVERSAL_CAPABILITY_PROFILE_SCHEMA_v0.1.json`；
- 回执：`DSVR_PROSPECTIVE_RECEIPT_SCHEMA_v0.1.json` 与大量 release/test/gate receipts（发布/测试/闸门回执）；
- 账本：`DSVR_PREDICTION_LEDGER_SCHEMA_v0.1.json`、`evidence_ledger.py`；
- 桥：`cognitive_semantic_bridge.py` 与 structural generation（结构生成）中的多种 bridge。

特别重要的继承规则：

- Worker output（工作器输出）不自动授予 production authority（生产权限）；
- Provider output（提供者输出）不是 Canonical authority（规范权威）；
- capability（能力）与 authority（权限）分离；
- candidate（候选）与 promoted（已提升）分离；
- receipt（回执）与 evidence（证据）分离。

## 本轮 DWAC 协作

DWAC Whole-Artifact Compiler（全工件编译器）v0.6.0 将 OPP 任务拆为 8 个工作单元：objective / existing / architecture / outline / semantic / execution / validation / delivery（目标 / 既有资产 / 架构 / 大纲 / 语义 / 执行 / 验证 / 交付）。其结果明确标记 `CANDIDATE`、`REFERENCE backend`（参考后端）且 `true_distributed_backend=false`（非真实分布式后端），因此本仓库保留该计划作为协作证据，而不把它误称为自动完成的最终实现。

## TINP transport archaeology（2026-09-11）

本轮 GitHub 考古核对 `xingxuling/TINP` `codex/next-internet-v01@1aa235d9f5718f87c959e275da10a7bf12d58e9f`：

- `src/transport.mjs` 已有 TINP-owned UDP/TCP/TLS loopback transport、DATA framing、peer public-key admission、timeout/overload boundary 和 TLS 1.3 loopback 证据；
- `adapters/opp-bridge.mjs` 与 `adapters/opp-negotiate.py` 复用 OPP CHP/RCP 协商，不复制 OPP agreement semantics；
- 当前资产没有证明公网 HTTP/REST、NAT、DNS、真实异机 enrollment 或生产网络 policy；其 OPP child adapter 仍 pinned 到旧 `f7b76582...`，不是本轮 OPP `main@61cc382...`；
- 因此 OPP 本轮只记录 TINP 为 transport donor/owner，禁止把 TINP loopback 证据改称第三方网络互操作，也禁止把 TINP transport 复制进 OPP Core。下一步应先做明确的 TINP↔OPP adapter version/policy binding。

## RCL OpenAPI donor archaeology（2026-09-11）

AI001 `codex/fix-ai001-index-v02@d80cd08` was inspected before extending the transport boundary:

- `src/openapi-source-frontend.mjs` parses OpenAPI 3.x JSON, resolves local references and emits one RCL capability specification per operation;
- its declared boundary says it does not execute HTTP, resolve remote references or prove full OpenAPI conformance;
- no executable HTTP provider, credential policy or receipt transport was found in the inspected source path.

Decision: retain AI001 as an RCL source-frontend donor only. TINP keeps HTTP transport/provider ownership, OPP keeps CHP/RCP and handoff semantics, and no parallel OpenAPI transport was added.
