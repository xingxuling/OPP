# TaoWind OPP — Open Reality Protocols（道风开放现实协议族）

> **OPP = Open Reality Protocols（开放现实协议族）**。本仓库把 TaoWind / RCL / RNCS / DWAC 中已经出现的协议、契约、接口、模式、能力、证据、回执、账本与桥接原语，收束成一套可读、可验证、可协商的开放协议候选。

当前协议族版本：`0.1.0-candidate.1`（核心协议 ID 不变）；当前 Runtime / Bridge / Semantic Tooling（运行时 / 桥 / 语义工具链）版本：`0.3.0-candidate.1`。当前状态：**CANDIDATE（候选）**，不是互联网标准、生产安全标准或外部权威认证标准。

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
- Semantic Bridge Verifier（语义桥验证器）：静态提取 Python / JavaScript / TypeScript / JSON Schema 接口形状；
- Auto Bridge Synthesizer（自动桥合成器）：生成可审计的声明式字段转换计划；
- Auto Connect（自动连接）：直接搜索两个项目之间的 `output → input` 兼容路径；
- Native Invocation Adapter（原生调用适配器）：显式调用受支持的 Python 顶层函数；
- Sandbox Interop Runner（沙箱互操作运行器）：真实执行 `Producer → Bridge → Consumer（生产端→桥→消费端）` 并生成回执；
- DWAC 协作编译证据与资产考古映射。

## 本地使用

```bash
python -m pip install -e .
python -m opp validate examples/capability.json
python -m opp validate examples/artifact.json
python -m opp semantic verify ./repo --profile auto
python -m opp semantic connect ./producer-repo ./consumer-repo --out ./connect.json
python -m unittest discover -s tests -v  # 已执行 pip install -e . 后运行 / run after editable install
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


## Semantic Bridge + Auto Connect（语义桥 + 自动连接）

Bridge Compiler v0.2 在“发现协议声明”之上增加静态语义接口层。当前可以从 Python 类型注解、TypeScript 类型签名和 JSON Schema（JSON 模式）生成 input/output port（输入/输出端口），再按 `exact / structural / lossy / incompatible / unknown`（精确 / 结构兼容 / 有损 / 不兼容 / 未知）判断连接关系。

自动生成的桥只使用 OPP 自有声明式操作：`identity / rename / select / inject-default`（恒等 / 重命名 / 字段投影 / 注入已声明默认值）。不会生成或执行任意 Python、Shell 或源仓库代码。

详见 `docs/SEMANTIC_BRIDGE.md` 与 `docs/AUTO_CONNECT.md`。


## Native Invocation + Real Interop（原生调用 + 真实互操作）

v0.3 第一次把 v0.2 找到的静态连接路径真正执行成：

`Producer invocation（生产端调用） → OPP declarative bridge（OPP 声明式桥） → Consumer invocation（消费端调用） → Interop Receipt（互操作回执）`

静态扫描仍然不会执行源码。只有显式 Invocation Spec（调用规范）并提供 `--allow-execution（允许执行）` 才会进入原生调用。当前只支持 `python-function（Python 函数）` 适配器，不使用 Shell（命令解释器），并使用路径包含检查、符号链接拒绝、清理环境、临时工作目录、超时、输出接受上限和 JSON 失败关闭。

```bash
opp invoke run examples/invocation-producer.json examples/interop-input.json --allow-execution
opp interop run examples/interop-run.json examples/interop-input.json --allow-execution --out interop-result.json
```

当前 Sandbox（沙箱）是 **bounded child process（有界子进程）**，不是 Linux namespace / seccomp / container / VM（Linux 命名空间 / 系统调用过滤 / 容器 / 虚拟机）级强安全沙箱。Interop PASS（互操作通过）只证明这一条具体调用链真实成功，不证明任意第三方代码安全或普遍兼容。详见 `docs/NATIVE_INTEROP.md`。
