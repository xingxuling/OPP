# OPP：先判断两个接口能否衔接，再执行受限的数据转换

> 文档代码基线：`main@da65ab1d26c01c5e2939294e415b9fd07b7dbe5a`，远端核对时间2026-10-03 12:32 UTC。附件报告没有记录源码commit，以下报告结果不自动归属于此基线。

你有两个已经存在的程序。一个输出 `unique_items`，另一个只接受 `values`。你需要知道：它们是否表示同一种数据，能不能只改字段名，哪些字段会被丢弃，以及接口变更后是否必须停止调用。

OPP 当前提供一个 Python 候选 SDK，帮助开发者完成这条流程：

1. 给两端提供输入/输出 Schema、接口版本、字段意义和单位
2. 判断可直接衔接、可无损改名、需明确同意裁剪、证据不足或不可衔接
3. 对可执行结果生成绑定双方声明的契约和声明式转换
4. 调用者明确允许执行后，调用已经注册的 Provider
5. 保存成功或失败回执，供离线核验

> 当前状态：Candidate；Python 包 `taowind-opp` / `0.3.0.dev1`；Core Protocols `0.1.0-candidate.1`；Runtime / Bridge / Semantic Tooling `0.3.0-candidate.1`

OPP 不会仅根据字段名猜业务含义。HTTP/CLI 的实际调用代码、超时、输出限制和身份权限策略仍由接入者提供。当前适合验证接口集成方案，不是任意系统的一键连接器。

## 先看一个确实存在的例子

仓库中的 `examples/cha-session/run_demo.py` 有两条独立会话：

| 会话 | 输入 | OPP 的转换 | 输出 |
|---|---|---|---|
| Python / Boltons → 本地 HTTP / JMESPath | `{"legacy_items":[3,1,3,2]}` | Python 去重后，将 `unique_items` 改名为 `values` | `{"ordered":[1,2,3]}` |
| 本地 HTTP / JMESPath → CLI / more-itertools | `{"values":[3,1,2]}` | HTTP 排序后，将 `ordered` 改名为 `entries` | `{"groups":[[1,2],[3]]}` |

这是真实库、真实本地进程和 HTTP 调用；接口包装与字段意义声明由本项目作者编写。它不是三家独立实现的 OPP，也不是一个跨三端的原子事务。

## 从零运行：Windows PowerShell

前置条件：Python 3.10+。在 OPP 仓库根目录按顺序执行。这个演示会启动本地进程和 loopback HTTP 服务，并在脚本内显式允许执行；只应对已审查的仓库代码运行。

```powershell
python -m venv .venv-doc-demo
$py = Join-Path $PWD '.venv-doc-demo/Scripts/python.exe'
& $py -m pip install .
& $py -m pip install -r examples/external-projects/requirements.txt
& $py examples/cha-session/run_demo.py --out .runs/cha-session-doc-demo --require-installed
```

`.runs/cha-session-doc-demo` 必须是尚不存在的目录。再次运行时使用新目录，不要覆盖先前证据。macOS/Linux 使用 `.venv-doc-demo/bin/python` 执行相同 Python 参数。

成功时检查：

- 输出 `status` 是 `PASS`
- `sessions` 中两条结果分别为上表的排序和分组输出，`outcome` 为 `ADAPT`
- 新目录包含原始接口描述、协商、契约、两条会话回执、HTTP 失败和显式恢复记录
- 本次成功并不自动证明其他输入、其他服务或真实公网可用

## 谁做什么

| 仍由开发者做 | 当前代码自动做 |
|---|---|
| 写 Python/HTTP/CLI 包装与传输限制 | 导入有界接口描述，校验 Schema |
| 声明字段 concept/unit、stateless 与权限上下文 | 按明确语义匹配，判定兼容结果 |
| 注册 Provider、选择消费者目标 | 生成受限字段映射并绑定契约根 |
| 同意具体字段裁剪、明确允许执行 | 执行前检查契约与接口漂移，检查中间结果 |
| 故障后选择健康 Provider 并重新调用 | 对每次成功/失败留下独立回执，不隐藏重试 |

## 五种结果：拿到结果后该做什么

- `DIRECT`：数据无需字段转换；仍要通过执行授权、当前权限与接口版本检查
- `ADAPT`：可以做已证明的无损字段改名；不代表单位换算或任意复杂数据改写
- `DEGRADE`：仅裁剪调用者逐项同意的额外字段；同意范围写入 `allowedDrops`
- `NEGOTIATE`：缺少语义、约束或裁剪同意；不会产生可执行契约。补充材料后重新协商
- `REJECT`：例如单位冲突、权限不足或目标不匹配；修正输入或接入条件后再试

“可执行契约”不等于“已经获准执行”。`run_session` 仍需要 `allow_execution=True`，并重新提供本次 `available_authority`；协商时的权限声明不会自动成为执行时的权限。

## 当前兼容范围

- Python：有当前候选原生函数调用路径
- HTTP/OpenAPI：已有本地真实执行案例；导入器支持 OpenAPI 3.1 的有界单 JSON-body operation，不是完整 OpenAPI 实现
- CLI：有调用者注册的本地 JSON 标准输入/输出 Provider 案例；不是自动执行任意命令
- MCP：已有 tools/list 描述导入测试；缺少 outputSchema 保持未知。尚未证明独立 MCP server 实际调用
- gRPC：尚未实现本轮接入
- Session：当前面向明确声明的无状态、封闭 JSON 对象；复杂有状态、副作用、流与未解释政策不能静默通过

## 失败不会怎样被掩盖

接口漂移会停止当前调用；生产者输出不符合 Schema 时不会继续调用消费者。HTTP 503 的恢复示例是调用者显式换回健康 Provider 后重新调用，不是自动故障转移，也没有原子回滚或通用 exactly-once 保证。回执有根代表可核对绑定关系，不代替可信身份、独立保存的可信根或强 OS 沙箱。

## 想先看预约表单 → CRM 的字段变换？

完成上述安装后运行：

```powershell
& $py examples/business_demo.py
```

这个例子的输入是姓名、电话、服务、预约时段和备注；输出把 `name/service/slot` 改成 `customer_name/service_code/preferred_time`，保留 `phone/notes`，加入 `channel`，不传 `debug_source`。脚本实际执行两个本地 Python fixture，返回新对象与回执，不连接真实 CRM。

注意：这些字段规则和默认值已经由作者写进 `examples/business_demo.py` 的 bridge，不是 OPP 自行理解预约业务或自动发现规则。该脚本内置 `allow_execution=True`。它展示预设桥接执行；前面的 Session 示例展示根据明确语义声明合成受限映射，Session 不会自行发明默认值。

[完整业务说明](BUSINESS_DEMO.md) · [完整输出](evidence/business-demo-output.json) · [Session 接入](docs/CHA_SESSION.md)

## 安装与失败排查

先安装，再运行 demo 或测试；否则 `ModuleNotFoundError: No module named 'opp'` 只表示当前解释器未安装该包。始终使用同一个虚拟环境解释器。

```powershell
& $py -m unittest discover -s tests -v
```

Windows 创建符号链接可能需要相应系统权限。若 `test_symlink_entrypoint_rejected` 在创建链接时出现 `WinError 1314`，应把它记为环境错误，不可写成全部测试通过，也不能直接推断业务调用失败。此处不要求为演示扩大系统权限。

## OPP 与 TINP 如何组合

OPP 的 Session 负责有界接口兼容、映射、契约与调用证据。TINP 的受控执行入口负责身份、权限、路由和恢复。当前可复核的一条组合链是：OPP 生成 native interop result，TINP 对既有结果校验并生成 acceptance binding。

该验收的 `authorityGranted:false` 与 `sideEffects:false` 表示验收本身不新增权限或动作；它不把此前执行变成已预授权，也不是任意 bridge 一键接入生产 TINP 网络。[TINP 仓库及接入说明](https://github.com/xingxuling/TINP)

## 四份提交材料：观察、来源与适用范围

以下材料由使用者提交用于本次评审，尚未连同其全部原始数据在本仓库归档。材料没有提供可核对的源码commit；“报告自述”与“本次静态代码核对”分开。另一项正在进行的本机基准不包含在这里，不填入其结果。

| 来源与精确位置 | 材料显示什么 | 能支持到哪里 |
|---|---|---|
| `opp.txt` L6–134、L139–218、L219–258 | 初次先运行后安装报`ModuleNotFoundError`；安装后66项：64通过、1跳过、1个`WinError1314`；业务demo为PASS | 该终端环境里的安装、测试与固定demo；不是完整测试全部通过 |
| `tinp.txt` L9–68、L70–71、L314–323 | alpha.29三步故障demo；旧式test入口；223项通过、0失败 | 该次本机运行；源码commit未知，不能当729113b完整复测 |
| `OPP-TINP兼容性测试报告.pdf` p4–9 | 补依赖后TINP223/223；OPP64通过/1失败/1跳过；握手150/150、协商180/180、联合12/12；篡改检测25/26 | 报告自述的受控样本，包含负例；不是通用可靠性或独立认证 |
| `report.md` L3–16、L42、L63–77 | 每场景1000次、25,000记录；HTTP完整链1000/1000、均值45.248ms；自述33/33复核 | Ryzen9700X/Python3.12.14、单机合成数据与本地HTTP；未随附samples/summary/manifest，未在本次重算 |

PDF p4/p10 的缺依赖失败需要保留为当次观察。其“未声明依赖”的解释与已查源码中存在requirements不同：旧代码通过默认`python`调用，声明依赖并不保证该解释器安装了依赖。新TINP测试引导是后续代码变化，不能用来否认报告当时失败。

性能口径也不能混用：PDF p6 的CLI进程端到端约230.0ms（n=12），p8 的TINP校验47.11µs；`report.md` 的本地HTTP全链路45.248ms（n=1000）来自另一台机器和另一条路径。它们不能组成“优化前后”的结论。恢复样本是调用者显式切换健康Provider后的重新调用，不是生产自动恢复率。

## 如何判断这里的“验证通过”

仓库的[Session证据账本](evidence/cha-session-2026-09-12/README.md)与[业务demo输出](evidence/business-demo-output.json)是对应固定场景的归档。运行命令才能获得你这次环境的结果；本文不把归档 PASS 当成当前机器的新测试。

报告测试或性能时请同时记录 commit、运行日期、解释器与依赖版本、场景、样本数、计时范围、原始数据和复核方式。正确拒绝负例、成功执行正例与兼容范围分别报告。CLI进程启动、纯协商和HTTP全链路是不同指标；不能跨机器、跨路径直接比较平均耗时。

回执离线核验应使用外部保管的预期根；仅把同一文件里可被一起替换的根互相比对不能建立独立信任。

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
<summary><strong>## 协议族内部结构：六个核心协议

OPP 的协议族内部名称为 Open Reality Protocols；CHA 指 Complex Heterogeneous Autonomous Systems。第一次运行不需要先记住这些术语。</strong></summary>

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

## 外部接入候选（2026-09-12，仓库报告）

新增 `opp.sdk` 公开入口与 `opp interop verify` 离线复核。三个独立维护的真实库完成安装包执行、桥接、错误输入拒绝与显式恢复；这仍由本机操作员完成，不是独立第三方验收。

[SDK 接入与复现](docs/PUBLIC_SDK.md) · [真实项目证据与限制](docs/EXTERNAL_ONBOARDING.md) · [下一步](ROADMAP.md)

## 历史托管验证记录（2026-09-12，仓库报告）

GitHub [远端执行 34692267549](https://github.com/xingxuling/TINP/actions/runs/34692267549) 的 Linux 生产端及 Linux / Windows 复核端全部成功。真实库运行与证据交接已离开当前电脑；仍不代表双物理设备、独立操作员或真实 Authority Provider。

Final code replay: [34692507409](https://github.com/xingxuling/TINP/actions/runs/34692507409), all three hosted jobs PASS; OPP `7c4970c`, TINP `692c0e4`. The earlier run is retained as historical evidence.
