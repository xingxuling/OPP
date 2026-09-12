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
- Unit tests（单元测试）：65 / 65 PASS（2026-09-12 CHA Session）
- RCP capability negotiation（RCP 能力契约协商）：candidate，OPP-owned exact ID/schema agreement（OPP 所有的能力 ID/模式精确协商）
- Wheel isolation install（安装包隔离安装）：PASS
- Concrete fixture interop（具体夹具互操作）：PASS，receipt root `77b4cdfaa0f95a9cc75a4c7d08f9d8cc3b94d40f2a9b46b87c51b2b1496f7ff2`
- RCL bridge（RCL 桥）：host / warrant / evidence（宿主 / 授权 / 证据）候选语义已表达；进程创建仍由 Python host runtime（Python 宿主运行时）所有
- Independent third-party interoperability（独立第三方互操作）：unverified / 未验证
- External standard status（外部标准地位）：none / 无
- GitHub Actions：not required / not used（不依赖 / 未使用）

## 2026-09-12 external onboarding candidate

Public SDK + original-input-bound offline verification implemented. Three installed third-party libraries passed concrete positive/negative/re-invocation scenarios. Static unknown types remain unknown; malformed plan roots fail before execution. See docs/EXTERNAL_ONBOARDING.md and evidence/external-onboarding-2026-09-12. External operator, production and TINP multi-host gates remain open.

## 2026-09-12 CHA Session candidate

OPP 定位为面向 CHA 的 Dynamic Interoperability Meta-Protocol。有界五类协商、RCP surface 导入、版本绑定会话契约、显式语义映射与旧 bridge 复用已实现。安装 wheel 后从源码树外实际运行 Python → HTTP、HTTP → CLI，结果和离线核验 PASS；HTTP 503 明确 FAIL，显式重新调用恢复 PASS。

完整材料见 [CHA Session](docs/CHA_SESSION.md) 和 [证据账本](evidence/cha-session-2026-09-12/README.md)。三项独立维护的库在本项目包装中运行；独立 OPP 实现/操作员未验证。MCP 仅声明导入测试，gRPC/多方协商/通用约束求解/生产授权均未完成。上述已有 native runtime 的限制保持；新增 SurfaceProvider 的传输边界由调用方实施。
