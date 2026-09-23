# OPP producer post-call drift hardening — 2026-09-23

## Governor routing

- Scheduling mode: `NORTH_STAR`（北极星）全局比较
- Implementation mode: `DEEP_DEVELOPMENT`（深度开发）
- Selected repository: `xingxuling/OPP`
- Selected bottleneck: CHA Session 在 producer（生产者）调用完成后、adapter（适配器）与 consumer（消费者）执行前，没有重新确认 producer capability declaration（能力声明）仍与已签入 session contract（会话合同）的声明一致。

## Why this repository won this window

- `Taowind-code` 与 `RCL` 在本轮前 12 小时内均有多次自治合并，按总督节流规则主动降频。
- `TINP` 当前更高严重度的 P0 主要依赖双独立物理端、真实 Authority Provider（权威提供器）与生产部署/恢复，当前窗口缺少可在仓库内单独闭合的现实条件。
- OPP 当前没有 GitHub Actions workflow（工作流），最近主线合并停留在 2026-09-15；本缺口可用小范围、可回滚、无外部副作用的代码变更闭合。

## Observed asymmetry

Before this candidate, `run_session`（运行会话）执行：

1. producer/consumer initial discovery（初始发现）
2. producer invocation（生产者调用）
3. producer output validation（生产者输出验证）
4. adapter
5. consumer rediscovery（消费者重新发现）
6. consumer invocation

因此，若 producer 在自己的调用期间改变 `revision` / declaration（版本/声明），旧路径不会再次读取 producer surface（表面），仍可能继续把该次输出送入 adapter/consumer。已有 consumer rediscovery 只能捕获 consumer 侧漂移，不能覆盖 producer 自身调用期间的漂移窗口。

## Candidate change

`src/opp/session.py` 在 producer output schema（生产者输出模式）验证后增加 `producer-rediscovery`：

- 再次调用同一个 caller-installed `SurfaceProvider.describe()`（调用方安装的表面提供器描述接口）；
- 将当前 declaration root（声明根）与 contract 内 producer declaration root 比较；
- 不一致时立即 `FAIL`，错误码 `CAPABILITY_DRIFT:producer`；
- 不调用 adapter 后的 consumer；
- successful receipt（成功回执）记录 `producer-rediscovery` stage 与 declaration root；
- offline verifier（离线验证器）验证 hardened six-stage journal（加固后的六阶段日志），同时保留对历史 five-stage v0.1 receipt（五阶段 v0.1 回执）的兼容读取。

不新增 authority（权限）、retry（重试）、rollback（回滚）、transport（传输）或 authentication（认证）声明。

## Targeted validation evidence

在总督运行环境执行与候选控制流等价的定向回归：

### Positive control（正向控制）

Stable producer + stable consumer：

- status: `PASS`
- stage sequence:
  - `discover-producer`
  - `discover-consumer`
  - `producer-output`
  - `producer-rediscovery`
  - `adapter`
  - `consumer-output`
- verifier hardened indexes: adapter=`4`, consumer-output=`5`

### Mutation negative（变异负控）

Producer invocation（生产者调用）返回输出前，把自身 surface revision 从 `1` 改为 `2`：

- status: `FAIL`
- error stage: `producer-rediscovery`
- error code: `CAPABILITY_DRIFT:producer`
- `executionMayHaveOccurred=true`
- consumer invocation count: `0`

这证明候选在已发生 producer 调用后不会假装“什么都没执行”，同时 fail-closed（失败关闭）阻止漂移后的数据继续进入 consumer。

## Compatibility / schema review

- Session artifact schema（会话工件模式）的 `steps.items` 本来就是 object（对象），新增 journal stage 不要求 schema 扩权。
- Contract format、receipt format 与 `implicitRetries=0` 保持不变。
- Offline verifier 接受旧 five-stage v0.1 successful receipt，并对新 six-stage receipt 额外验证 producer post-call declaration root。
- 无 GitHub Actions workflow；候选提交均带 `[skip ci] [skip actions]`，未主动创建或重跑 Actions。

## Multi-civilization review record（多文明联邦审查记录）

- Founder Twin：选择“缩短 capability truth（能力真值）漂移窗口”，不扩张协议范围。
- 柳清莲 Gate：无新 authority、无隐式重试、无外部不可逆动作。
- 洞哥 Grounding：问题来自当前 main 的真实控制流非对称，而非 Roadmap 推测。
- 产品 / UX：无用户界面行为变化。
- 工程 / 代码：单一控制流闸门 + verifier 兼容路径。
- 测试：正向控制 + producer mutation negative（生产者变异负控）。
- 安全：漂移后 fail-closed；错误仍保留 `executionMayHaveOccurred=true`。
- 发布：不做正式 Release。
- Integration Court：候选作用域局部、可回滚、不依赖 Actions；允许进入 PR 审查。

## Truth boundary（真值边界）

本候选**不证明** strong OS sandbox（强操作系统沙箱）、独立第三方 OPP 实现、stateful/streaming/side-effect session（有状态/流式/副作用会话）、provider identity authentication（提供器身份认证）、exactly-once（严格一次）或跨崩溃恢复。它只闭合 producer 调用期间 capability declaration drift（能力声明漂移）未被重新检查这一局部缺口。
