# OPP

**Software Interoperability & Capability Bridging Toolkit**  
**软件互操作与能力桥接工具**

> Protocol family name: **Open Reality Protocols**（协议族内部名称）  
> 当前状态：**Candidate**  
> Core Protocols：`0.1.0-candidate.1`  
> Runtime / Bridge / Semantic Tooling：`0.3.0-candidate.1`

当你不断把新的 API、Agent、开源项目和内部系统接在一起时，真正重复的工作往往不是“会不会写代码”，而是：

- 重新读双方接口；
- 找字段和类型差异；
- 判断哪些能直接接，哪些会丢信息；
- 写 Adapter；
- 接口一变，再来一次；
- 出问题后还要还原当时到底用了什么转换。

OPP 做的事很直接：

> **先把双方看懂 → 判断兼容性 → 生成受限桥接方案 → 明确授权后执行 → 留下回执。**

## 先看一个业务 Demo

最容易理解 OPP 的方式，不是先读协议，而是看一个普通系统对接：

```text
旧预约表单                 新 CRM
name            ->         customer_name
service         ->         service_code
slot            ->         preferred_time
缺少 channel    ->         注入默认来源
多余 debug      ->         不传给 CRM
```

直接运行：

```bash
python -m pip install -e .
python examples/business_demo.py
```

当前固定示例的实际运行结果：

```json
{
  "OPP 转换后": {
    "customer_name": "陈小姐",
    "phone": "+852 6123 4567",
    "service_code": "physio-first-visit",
    "preferred_time": "2026-09-15 14:30",
    "channel": "legacy-web-form"
  },
  "新系统结果": {
    "accepted": true
  },
  "状态": "PASS",
  "回执根": "5e8669216c4b7a8c0b4675da8c05b4e7a0f41b6afb56ccce2b4a4fe31256521f"
}
```

这不是示意 JSON。完整可复核输出保存在 [`evidence/business-demo-output.json`](evidence/business-demo-output.json)，完整业务说明见 [`BUSINESS_DEMO.md`](BUSINESS_DEMO.md)。

这个 Demo 不访问真实 CRM，也不代表任意 CRM 都能自动接入。它只证明当前候选运行时中的这条具体 `Producer -> Bridge -> Consumer` 链路可以真实完成。

## 为什么我不直接写一个 Adapter？

如果你只有两个稳定系统，直接写几十行 Adapter 往往更简单，**这时候不一定需要 OPP**。

OPP 开始有价值，是在下面这些情况：

- 接入对象越来越多；
- API / Schema 经常变化；
- Agent 会动态发现新的工具；
- 想在执行前先知道是“精确兼容、可转换、有损、不兼容还是未知”；
- 想把重复发生的接口判断变成可复用流程；
- 执行以后还需要知道这次到底用了什么转换、结果对应哪份回执。

它不是为了把简单集成复杂化，而是为了减少**不断重复理解接口和写胶水代码**的工作。

## 和你已经认识的工具有什么区别？

| 技术/方式 | 主要解决什么 | OPP 补在哪里 |
|---|---|---|
| **直接写 Adapter** | 两个具体系统之间的手工转换 | 接入对象多时，先自动检查差异和可转换性 |
| **SDK / REST / gRPC** | 已知接口怎么调用 | 判断两个端点是否真的兼容 |
| **OpenAPI / JSON Schema** | 描述接口和结构 | 读取结构后做兼容性和桥接判断 |
| **MCP** | Agent 怎么发现和调用工具 | 工具接入前后的能力、输入输出和桥接检查 |
| **A2A** | Agent 与 Agent 怎么协作通信 | 更关注能力契约和数据形状是否能互操作 |
| **TINP** | 身份、权限、路由、恢复、执行证据 | OPP 回答“能不能接”，TINP 处理“谁能调用、失败怎么办” |

更完整说明见 [`docs/COMPARISON.md`](docs/COMPARISON.md)。

## OPP + TINP 怎么一起用？

```text
企业现有系统 / API / Agent / MCP
              ↓
             OPP
        能不能接？怎么转？
              ↓
             TINP
     谁能调用？失败怎么办？
              ↓
       实际执行 + 回执 + 恢复
```

简单说：

```text
OPP：这个系统会什么？两个系统能不能接？怎么转换？
TINP：谁能调用？怎么传？失败怎么办？怎么恢复？
```

OPP 可以独立使用。需要身份、权限、路由和恢复时，再进入 TINP 的职责范围。

TINP：<https://github.com/xingxuling/TINP>

## 技术最小 Demo（3 分钟）

如果想看更纯粹的接口扫描和互操作夹具：

```bash
python -m pip install -e .
python -m opp semantic verify examples/semantic-fixtures --profile generic
python -m opp interop run examples/interop-run.json examples/interop-input.json \
  --allow-execution \
  --out interop-result.json
```

完整说明见 [`DEMO.md`](DEMO.md)。

## 当前工具链能做什么

- 从 Python、JavaScript、TypeScript 和 JSON Schema 提取接口形状；
- 判断两个接口是精确兼容、结构兼容、有损、不兼容还是未知；
- 生成受限的声明式转换：`identity`、`rename`、`select`、`inject-default`；
- 自动搜索 `producer output -> consumer input` 的连接路径；
- 显式授权后执行受支持的 Python 顶层函数；
- 运行真实的 `Producer -> Bridge -> Consumer` 链路；
- 为协商、转换和执行留下可验证回执。

静态扫描不会执行目标仓库代码。只有显式提供 Invocation Spec，并传入 `--allow-execution` 时才进入原生调用。

## 适合谁 / 不适合谁

### 适合

- 需要持续接入不同 API、Agent 工具和内部系统的平台；
- 需要在执行前自动检查接口兼容性的团队；
- 正在做 API / Schema 迁移或开源项目复用审计；
- 需要受限转换和互操作回执的自动化系统；
- 想做真实试点并量化集成成本的团队。

### 暂时不适合

- 两个系统已经有稳定官方 SDK，而且结构长期不变；
- 只想找成熟生产级 ESB / iPaaS 产品的客户；
- 需要任意语言、任意运行时都能自动执行的通用平台；
- 需要已经通过独立第三方安全认证的系统。

## 从 Candidate 到生产还差什么？

当前更适合原型、PoC 和外部试点，不适合包装成已经成熟的生产 iPaaS。

下一阶段重点不是继续增加协议名，而是增加外部证据：

```text
仓库内 fixture
    ↓
真实第三方项目互操作
    ↓
3–5 组外部 PoC
    ↓
记录人工基线与 OPP 指标
    ↓
扩展运行时 / 隔离 / 安全审查
    ↓
再讨论生产级发布
```

路线见 [`ROADMAP.md`](ROADMAP.md)。试点应该测什么见 [`docs/PILOT_METRICS.md`](docs/PILOT_METRICS.md)。

在没有真实试点数据之前，本项目不会写“节省 70% 开发时间”“降低 90% 集成成本”这类没有证据的 ROI 数字。

## 试点阶段准备量什么？

| 指标 | 关注的问题 |
|---|---|
| 首次接入耗时 | 手工 Adapter 与 OPP 流程各花多久 |
| Schema 漂移发现时间 | 接口变化后多久能发现 |
| 可自动桥接比例 | 哪些差异可以由受限 bridge 处理 |
| 人工介入次数 | 哪些环节仍需要开发者判断 |
| 失败可解释率 | FAIL / UNKNOWN 能不能说清原因 |
| 回执覆盖率 | 执行链是否留下可复核 receipt |
| 二次维护工作量 | 接口变化后修复成本如何变化 |

详细记录模板见 [`docs/PILOT_METRICS.md`](docs/PILOT_METRICS.md)。

<details>
<summary><strong>协议族内部结构：六个核心协议（第一次使用 OPP 可以先不看）</strong></summary>

| 协议 | 人话解释 | 作用 |
|---|---|---|
| **RXP** | 一次跨系统交换里要带什么 | 承载状态、意图、能力、约束、证据和动作描述 |
| **RCP** | **这个系统会什么** | 描述能力、输入输出和限制 |
| **RAP** | **这个工件是什么、依赖什么** | 描述代码、文档、模型、数据库等工件 |
| **REP** | **这个结果凭什么可信** | 把主张与来源、方法和可复现信息绑定 |
| **RSP** | **当前到底是什么状态** | 表达对象、关系、事实、观察、预测和状态根 |
| **CHP** | **两个陌生系统先谈清楚再开始** | 交互前协商版本、能力和约束 |

`Reality` 和 `Civilization` 是协议族内部历史命名，不代表现实世界权威，也不代表外部标准地位。

</details>

## 当前边界

OPP 当前**不声称**：

- 任意第三方项目都能自动兼容；
- 已具备 Linux namespace / seccomp / container / VM 级强沙箱；
- 已通过独立第三方互操作认证；
- 已成为互联网或行业标准；
- 一次本机 PASS 等于生产安全。

详细边界见 [`STATUS.md`](STATUS.md)、[`SECURITY.md`](SECURITY.md) 和 [`docs/NATIVE_INTEROP.md`](docs/NATIVE_INTEROP.md)。

## 文档入口

- [`BUSINESS_DEMO.md`](BUSINESS_DEMO.md) — 业务 Demo：旧预约表单接新 CRM
- [`evidence/business-demo-output.json`](evidence/business-demo-output.json) — 当前业务 Demo 的可复核输出
- [`DEMO.md`](DEMO.md) — 技术最小 Demo
- [`docs/COMPARISON.md`](docs/COMPARISON.md) — 和 Adapter / SDK / MCP / A2A 的关系
- [`docs/PILOT_METRICS.md`](docs/PILOT_METRICS.md) — 外部试点怎么量价值
- [`docs/USE_CASES.md`](docs/USE_CASES.md) — 什么时候值得用 OPP
- [`docs/REAL_WORLD_EXAMPLES.md`](docs/REAL_WORLD_EXAMPLES.md) — 现实业务映射
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 架构和模块分工
- [`docs/SPECIFICATION.md`](docs/SPECIFICATION.md) — 协议规范
- [`ROADMAP.md`](ROADMAP.md) — 后续路线
- [`SECURITY.md`](SECURITY.md) — 安全边界与报告方式

## License

MIT License，见 [`LICENSE`](LICENSE)。

## 外部接入候选（2026-09-12）

新增 `opp.sdk` 公开入口与 `opp interop verify` 离线复核。三个独立维护的真实库完成安装包执行、桥接、错误输入拒绝与显式恢复；这仍由本机操作员完成，不是独立第三方验收。

[SDK 接入与复现](docs/PUBLIC_SDK.md) · [真实项目证据与限制](docs/EXTERNAL_ONBOARDING.md) · [下一步](ROADMAP.md)

## 无设备替代验证已完成（2026-09-12）

GitHub [远端执行 34692267549](https://github.com/xingxuling/TINP/actions/runs/34692267549) 的 Linux 生产端及 Linux / Windows 复核端全部成功。真实库运行与证据交接已离开当前电脑；仍不代表双物理设备、独立操作员或真实 Authority Provider。

Final code replay: [34692507409](https://github.com/xingxuling/TINP/actions/runs/34692507409), all three hosted jobs PASS; OPP `7c4970c`, TINP `692c0e4`. The earlier run is retained as historical evidence.
