# OPP v0.3 Tooling Status（工具链状态）

- Core protocol suite（核心协议族）：`0.1.0-candidate.1`，6 个核心协议；v0.3 不增加核心协议
- Runtime / Bridge / Semantic Tooling（运行时 / 桥 / 语义工具链）：`0.3.0-candidate.1`
- Python package（Python 包）：`0.3.0.dev1`
- Bridge Compiler（桥编译器）：candidate（候选实现）
- Semantic Bridge Verifier（语义桥验证器）：candidate
- Auto Bridge Synthesizer（自动桥合成器）：candidate，声明式转换，不生成任意代码
- Auto Connect（自动连接）：candidate，跨仓库 `output → input` 搜索
- Native Invocation Adapter（原生调用适配器）：`python-function` candidate
- Sandbox Interop Runner（沙箱互操作运行器）：candidate，真实 `Producer → Bridge → Consumer` 执行
- Execution consent（执行同意）：required / 必须显式允许
- Shell usage（Shell 使用）：disabled / 禁止
- Path containment + symlink rejection（路径包含 + 符号链接拒绝）：implemented / 已实现
- Environment / CWD（环境 / 工作目录）：sanitized + ephemeral（清理 + 临时）
- Timeout / output acceptance gate（超时 / 输出接受闸门）：implemented / 已实现
- Strong OS sandbox（强操作系统沙箱）：**not claimed / 不宣称**
- Authority promotion（权限提升）：none / 无
- Hidden retries（隐藏重试）：none / 无
- Unit tests（单元测试）：46 / 46 PASS（43 个既有测试 + 3 个 TINP handoff receipt boundary 负例，2026-09-11 本机候选分支复验）
- RCP capability negotiation（RCP 能力契约协商）：candidate，OPP-owned exact ID/schema agreement（OPP 所有的能力 ID/模式精确协商）
- Wheel isolation install（安装包隔离安装）：PASS
- Concrete fixture interop（具体夹具互操作）：PASS，receipt root `77b4cdfaa0f95a9cc75a4c7d08f9d8cc3b94d40f2a9b46b87c51b2b1496f7ff2`
- RCL bridge（RCL 桥）：host / warrant / evidence（宿主 / 授权 / 证据）候选语义已表达；进程创建仍由 Python host runtime（Python 宿主运行时）所有
- Independent third-party interoperability（独立第三方互操作）：unverified / 未验证
- External standard status（外部标准地位）：none / 无
- GitHub Actions：not required / not used（不依赖 / 未使用）

## Latest Reality Audit（2026-09-11）

本轮以 GitHub `xingxuling/OPP` `main@61cc3828a58a7bffa8b1dbeb8c44ff3a9cb471d1` 为源码基线，在独立候选分支 `codex/opp-windows-utf8-v01` 上审计并修复 Windows 编码边界。

- 基线运行：41 个测试中 37 个通过，4 个 CLI 用例因默认 `cp950` 无法编码双语 JSON 输出而失败；这是宿主输出边界故障，不是协议兼容性通过。
- 本轮修改：隔离 child runner（子运行器）显式以 UTF-8 字节读写；CLI stdout 使用 ASCII-safe JSON，`--out` 文件仍使用 UTF-8；加入中文 payload 和旧 code page 回归测试。
- 当前证据：43 / 43 本机测试通过；`compileall` 通过；强制安装本轮 wheel 到独立虚拟环境后，安装包 `opp validate` 通过；具体 fixture interop receipt root 保持 `77b4cdfaa0f95a9cc75a4c7d08f9d8cc3b94d40f2a9b46b87c51b2b1496f7ff2`。
- 本轮不宣称：跨主机、独立第三方、强操作系统沙箱、网络隔离、staging 或 production verified。
- 集成法院与机器证据：`docs/INTEGRATION_COURT_2026-09-11.md`、`evidence/OPP_WINDOWS_UTF8_AUDIT_2026-09-11.json`。

### Third-party Boundary Follow-up（第三方边界跟进）

- 宿主对 GitHub REST `GET /repos/xingxuling/OPP` 获得 HTTP `200`，但 OPP 显式授权的 child process 在清理环境中以 `GITHUB_NETWORK_ERROR:gaierror` 失败关闭；没有继承代理、凭据或隐藏重试。
- 这只产生负证据，不产生 `THIRD_PARTY_VERIFIED` 互操作声明。详见 `docs/INTEGRATION_COURT_2026-09-11_THIRD_PARTY.md`、`evidence/OPP_THIRD_PARTY_BOUNDARY_2026-09-11.json`。
- RCL/K400 候选压力账本见 `docs/RCL_STRESS_FIELD_2026-09-11.md`；九门均不自宣 PASS。
- 后续 TINP policy-bound HTTP adapter 已将同一 projected response 通过显式 handoff 交给 OPP consumer；OPP 侧现在独立复验 HTTP status/media/error/size/boundary/shape 语义，并拒绝重算根后的伪造回执。最新 TINP 默认路径改为 Node 内置 `https.request` 与每请求显式 Agent，且标准全局 proxy API 的 loopback 负例仍得到 HTTP 200。另用系统 curl/libcurl 做了禁止代理、禁止重定向的独立 runtime replay，选定字段 root 与 TINP native root 一致；这仍不是第三方 Owner 或生产证明。handoff PASS 见 `docs/INTEGRATION_COURT_2026-09-11_TINP_HANDOFF.md`、`evidence/OPP_TINP_HTTP_HANDOFF_NATIVE_2026-09-11.json`、`evidence/OPP_TINP_HANDOFF_HARDENING_2026-09-11.json` 与 `evidence/OPP_INDEPENDENT_CURL_REPLAY_2026-09-11.json`；仍不升级为独立第三方或生产声明。

## Production Gap Frontier（当前真实缺口）

| Gap ID | 缺口 | 当前状态 | 最小下一验证 |
|---|---|---|---|
| OPP-WIN-UTF8-001 | Windows legacy code page 下的 child/CLI UTF-8 传输 | 本轮本机候选验证通过 | 独立安装环境的更多 Windows locale 与真实第三方 CLI consumer |
| OPP-THIRD-PARTY-001 | 独立第三方系统互操作 | TINP policy-bound provider → OPP explicit consumer handoff PASS；direct child FAIL_CLOSED | 第二个独立 provider/producer 与 Court replay |
| OPP-TRANSPORT-001 | 第三方网络 transport、代理与权限边界 | TINP candidate policy/receipt 已实现，未合并/未生产 | 独立审查、跨主机/凭据生命周期与故障实验 |
| OPP-SANDBOX-001 | 强 OS sandbox / 网络与文件系统隔离 | 未宣称 | 评估成熟外部 sandbox adapter，不在 OPP 内重造 sandbox |
| OPP-DISTRIBUTED-001 | 跨主机 transport、分区、重启和凭据轮换 | 未验证 | 复用 TINP 或成熟 transport，完成双主机最小故障实验 |
