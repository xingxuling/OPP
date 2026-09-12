# CHA Session candidate v0.1

OPP 是面向 Complex Heterogeneous Autonomous Systems 的 Dynamic Interoperability Meta-Protocol。表层协议负责收发与调用，OPP 负责判断描述能否组合、生成有边界的协作契约与声明式适配，并保留证据。Agent 是主体的一种；多 Agent 编排不是核心假设。

当前实现是有界候选：两个现有业务规格可以不同，语义证据必须明确。它不会从名字、自然语言或相似 Schema 猜出业务等价，也没有实现任意协议互通或无需共同意义的协商。

## 审计与最短路径

基线为 `main@2e067522e2b79d927569be02a423c58ebbca268e`，原有 45 项测试通过。检查了六个核心协议及 Schema、CHP/RCP、源码扫描、兼容判定、桥接合成、Python child runtime、安装资源、原始回执核验、README/STATUS/ROADMAP，以及 ARCHAEOLOGY、初始 native interop 和后续精确 RCP/完整性修复的历史。

| 既有资产 | 裁决 | 本轮最小补充 |
|---|---|---|
| CHP 协议求交 | REUSE | 不要求 `sharedCapabilities` 非空，演示双方业务 ID 完全不同 |
| RCP 能力包和完整性 | REUSE | 在 `extensions.session` 增加可选 profile、表层绑定和字段语义 |
| `negotiate_capability` 精确 ID/Schema | KEEP | 不改变旧含义，新增 `negotiate_session` 处理输出到输入组合 |
| `SemanticPort` / `synthesize_bridge` / `apply_transform` | ADAPT | 先做显式语义字段匹配，再复用原有结构桥和转换解释器 |
| `compare_ports` 的宽松结构候选 | KEEP + GUARD | 会话先证明字段约束；未知约束不能凭 structural 候选获得执行资格 |
| `InvocationSpec` / `run_invocation` | REUSE | Python 继续使用原有子进程；其他传输由调用方注册 Provider |
| 回执规范化根与已有第三方 provenance collector | REUSE | 会话输入、发现声明、契约、Adapter、阶段结果共同可核验 |

没有新增第七个核心协议，没有改写原有 runtime/bridge，也没有新增生产依赖。会话对象是 RCP 之上的 tooling profile，不是另一个传输协议。

## 最小公共语义

双方各自提供合法 `opp.rcp.v0.1` capability envelope。`extensions.session` 包含：

```json
{
  "profile": "opp.session.v0.1",
  "surface": {
    "kind": "openapi-json",
    "bindingId": "caller-installed-sorter",
    "revision": "1",
    "discoveryRoot": "sha256-of-observed-native-description"
  },
  "semantics": {
    "input": {"values": {"concept": "urn:example:integer-sequence", "unit": "1"}},
    "output": {"ordered": {"concept": "urn:example:integer-sequence", "unit": "1"}}
  }
}
```

`concept` 是提供方或接入者明确声明的字段意义，`unit` 是单位（无量纲为 `1`）。这两个字段不是 OPP 自动发现的事实。双方业务名、Schema 字段名和 Surface Protocol 不必相同；共同概念或人工确认的语义仍不可省略。映射证据缺失时返回 NEGOTIATE，补充声明后重新提交，旧声明与旧契约不会被偷偷修改。

导入器的 `issuedAt` 使用 epoch 哨兵以保持相同声明的稳定根，不代表发现时间或可信时间。完整声明根比较是保守策略：元数据变化也需要重新协商。

`describe_surface` 支持显式 Python/CLI/自定义 Provider 描述；`describe_openapi` 读取 OpenAPI 3.1 的单个 JSON-body operation；`describe_mcp_tool` 读取已发现的 tools/list 项。导入器本身不联网、不启动命令、不自动证明只读或赋权。默认 statefulness 为 unknown，必须由接入方明确声明才能进入本轮 stateless profile。

OpenAPI 实现仅接受单一明确 2xx JSON 响应和 required JSON requestBody。参数、认证、回调、链接、多种成功结果不支持时明确报错；Schema `$ref`、组合/条件等未证明部分不能执行。MCP 无 outputSchema 保留 unknown；annotations 不被当作权限或副作用证明。OpenAPI/MCP 的语义字段通过接入层声明，不伪称为标准原生字段。

标准依据：[OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) 与 [MCP tools/list 和结构化输出](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)。本实现固定上述有界子集，不声明覆盖最新标准的全部特性。

## 五类结果

| 结果 | 判定 | 可执行契约 |
|---|---|---|
| DIRECT | 已有语义与约束证据，数据无需字段转换；安全 integer→number 也无需改变值 | 有 |
| ADAPT | 意义与单位一致，生成无损字段重命名并通过结构/约束证明 | 有 |
| NEGOTIATE | 未知/歧义语义、未保证字段、未证明约束、待明确裁剪同意、未实现政策 | 无；补证据后重提 |
| DEGRADE | 唯一允许的本轮降级是调用方逐项同意丢弃明确额外字段 | 有，绑定 `allowedDrops` |
| REJECT | 类型或单位冲突、权限缺失、目标不匹配、profile 不支持、离线或弃用声明 | 无 |

`goal` 当前是调用方明确选定的消费者 capability ID，不是自然语言规划器。字段约束必须相同，或仅将 integer 安全拓宽为 number；不会把单位转换、默认值发明、复杂约束推理伪装成适配。Session v0.1 处理 closed JSON objects；嵌套字段可原样传递，但不生成嵌套改名、数组元素重写、交换改名或多对一映射。

副作用、持久状态、流、rights、成本/时延政策、未解释的 envelope constraints 均不静默忽略，而进入 NEGOTIATE。此处是在明确暴露待实现的边界，未提供这些特性的通用协商求解器。

## Session Contract 与执行

公开入口位于 `opp.sdk`：`describe_surface`、`describe_openapi`、`describe_mcp_tool`、`negotiate_session`、`SurfaceProvider`、`run_session`、`verify_session_contract`、`verify_session_receipt`。SDK_API_VERSION 仍为 1，旧函数行为保持。

`taowind.opp.session-contract.v0.1` 固定生产者/消费者完整 RCP 声明、版本/发现根、目标、可用权限声明、逐项裁剪同意、语义映射、原有结构 bridge 及其根。`contractRoot` 覆盖整个契约；执行前重算协商，篡改后重新加散列的 Adapter 也不能绕过规则。

调用方安装 `SurfaceProvider(binding_id, describe, invoke)`，并显式 `allow_execution=True`。远端描述只能选择已经注册的 binding，不能变成命令、任意代码或网络目的地址。调用方仍须信任 Provider 代码；`describe` 必须读取当前真实描述，`invoke` 必须实施传输期限、输出上限、身份/权限策略，并将远端错误抛出。本轮示例限制为显式 loopback HTTP 与本地已审查进程，不继承代理或应用凭据。

执行顺序：

1. 检查契约可重建及当前调用方权限上下文。
2. 重新发现双方能力，完整声明根有漂移则停止。
3. 检查生产者输入，调用一次，检查生产者输出。
4. 执行已有 `rename/identity/select` 转换，检查消费者输入。
5. 再次发现消费者，检测两次调用间漂移；调用一次并验证结果。
6. 记录有根的阶段日志，成功与失败均保留，不隐式重试。

本轮不提供原子执行或防止“检查后瞬间漂移”的远端锁。真实 Provider 若要求强版本一致性，应在服务端实施版本前置条件。权限列表是调用方上下文，不是认证凭据；注册绑定与根也不证明远端身份。双方签名接受、动态撤权和去中心化信任仍是外部集成工作。

Schema 见 [session-artifacts.schema.json](../schemas/session-artifacts.schema.json)，随 wheel 打包。结构校验之外必须执行根和契约重建核验。离线成功验证需要外部保管的 expected contract/receipt roots；换掉整组证据及全部可信根仍能伪造自洽故事。FAIL 日志不能被成功验证器提升为 PASS。

## 复现真实异质闭环

在隔离环境安装 wheel 和现有固定版本第三方依赖，然后从任意目录运行：

```powershell
python -m pip wheel --no-deps . -w dist
python -m pip install --force-reinstall dist/taowind_opp-0.3.0.dev1-py3-none-any.whl
python -m pip install -r examples/external-projects/requirements.txt
python examples/cha-session/run_demo.py --out <新的证据目录> --require-installed
```

程序启动真实进程，读取 Python 描述、HTTP `/openapi.json` 和 CLI `--describe`，保存原始发现材料、CHP、RCP、协商与契约、原生调用回执、会话回执及第三方安装文件 provenance。两个端点各自的业务规格没有统一改写：

```text
Boltons Python: legacy_items → unique_items
                   OPP: unique_items → values
JMESPath HTTP: values → ordered             => {ordered: [1,2,3]}

JMESPath HTTP: values → ordered
                   OPP: ordered → entries
more-itertools CLI: entries → groups         => {groups: [[1,2],[3]]}
```

这是两条会话，不是三节点事务。CHP 的 sharedCapabilities 为空仍可协作，因为后续连接的是不同能力的输出与输入。三项第三方库是真实安装包；三个业务包装由本仓库作者编写，因此不是独立第三方 OPP 实现验证。

另有真实 HTTP 503 负例，记录 consumer-call FAIL 和可能已执行边界，然后由调用方选择健康的无状态 Provider，显式发起新一次调用。它证明有边界的重新调用恢复，不证明自动 failover、持久恢复或 exactly-once。

已归档输出见 [证据账本](../evidence/cha-session-2026-09-12/README.md)。离线命令：

```powershell
python scripts/verify_cha_session.py <证据目录> --expected-summary-sha256 <外部保管的摘要哈希>
python -m unittest discover -s tests -v
```

## 复用与未完成边界

OPP 保留兼容/映射/契约所有权，TINP 保留授权接入、路由、网络 failover 和恢复所有权，RCL 的已有 admission/profile 所有权不动。Python/HTTP/CLI 是执行 Provider；未宣称 RCL-native，也未从本次局部实现提炼新的 Core primitive。

本轮不开启凭据、付费或真实硬件门槛。下一缺口优先是独立维护的 MCP server 实际调用、真实外部接入者评审语义声明，以及 TINP 版本/权限前置条件；gRPC、多方协商、任意 JSON Schema 包含关系求解均未实现。没有用新的抽象层掩盖这些限制。
