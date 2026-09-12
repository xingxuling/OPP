# OPP Roadmap

这不是发布日期承诺，而是根据当前 `STATUS.md` 和已实现能力整理出的**下一阶段缺口**。

## P0 — 证明它不只对自己的测试项目有效

当前最重要的不是继续增加协议数量，而是扩大真实互操作证据。

目标：

- 选取几个独立第三方仓库作为固定测试对象；
- 覆盖 Python / TypeScript / JSON Schema 的真实接口；
- 记录 exact / structural / lossy / incompatible / unknown 的实际案例；
- 对自动生成的 bridge plan 做人工复核；
- 保存可复现的 interop receipt。

完成这一阶段后，才能更有把握地讨论 OPP 的通用性。

## P1 — 扩大可调用运行时

当前 Native Invocation Adapter 主要支持 `python-function`。

下一步可以逐步增加更多**显式、受限、可审计**的调用适配器，而不是直接开放任意 Shell。

每新增一种运行时，都应该同时提供：

- 输入输出边界；
- 路径和环境限制；
- 超时与输出上限；
- 正常案例；
- 失败案例；
- 回执验证。

## P1 — 更强的隔离证明

当前运行时是 bounded child process，不声称拥有 Linux namespace / seccomp / container / VM 级强隔离。

如果未来要面向更高风险的第三方代码执行，需要把隔离能力单独做成可验证层，并保持默认失败关闭。

## P1 — 开发者入口

为了让外部开发者更容易试用，优先补：

- 更小的真实仓库示例；
- 一条命令完成 scan + connect 的演示；
- GitHub / CI 场景的兼容性检查示例；
- MCP / A2A 工具接入示例。

## P2 — 稳定版本与外部互操作

在进入稳定版本前，需要至少回答：

- 哪些协议字段已经足够稳定；
- 哪些字段仍允许破坏性变化；
- 第三方实现能否独立产生和消费 OPP 对象；
- 是否存在至少一个非本仓库实现完成互操作；
- 兼容性规则和 bridge 行为是否有长期版本策略。

## 当前不作为短期目标

- 宣称成为互联网标准；
- 默认执行任意第三方代码；
- 自动提升权限；
- 用更多协议数量代替真实互操作证据。

当前状态以 [`STATUS.md`](STATUS.md) 为准。

## 2026-09-12 external onboarding update

## Completed in the external-onboarding candidate

- Public `opp.sdk` surface backed by existing OPP implementations; legacy imports retained.
- Windows UTF-8 repair reused from the previous candidate branch.
- Unknown type comparison stays unknown; bridge plan root checked before execution.
- Offline, original-input-bound success receipt verification through SDK and CLI.
- Three real installed libraries, positive/negative/recovery runs and cross-language receipt checks.
- Installable wheel tested outside the source tree; repeatable evidence script and package provenance.

## Next smallest gaps

1. Improve discovery from existing type stubs and explicit external JSON contracts before adding another IR.
2. Run a real independently maintained MCP server with the official client and preserve negotiation failures.
3. Stabilize public SDK regression contracts over multiple releases and recruit an independent consumer.
4. Join a real external capability to TINP's authorized routing/failover path, without moving OPP ownership.

## External gates

An independently operated consumer/security review has not run. TINP authority,
physical devices, trusted time and key custody cannot be substituted by OPP hashes.
Local measurements are not production performance or availability commitments.

## 无设备替代验证已完成（2026-09-12）

GitHub [远端执行 34692267549](https://github.com/xingxuling/TINP/actions/runs/34692267549) 的 Linux 生产端及 Linux / Windows 复核端全部成功。真实库运行与证据交接已离开当前电脑；仍不代表双物理设备、独立操作员或真实 Authority Provider。
