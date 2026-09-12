# Security Policy

OPP 当前是 Candidate，不应被当作已经完成生产安全认证的执行平台。

## 报告安全问题

如果你发现可能导致以下问题的缺陷，请不要在公开 Issue 中直接放出可利用细节：

- 路径逃逸；
- 符号链接绕过；
- 未授权执行；
- 环境变量或凭据泄漏；
- 输出上限 / 超时绕过；
- 桥接计划绕过允许操作集；
- 回执或完整性校验绕过。

如果仓库启用了 GitHub Private Vulnerability Reporting，请优先通过该入口提交。若没有启用，可以先开一个不包含利用细节的 Issue，请求建立私下沟通渠道。

## 当前安全边界

OPP 当前明确不声称：

- Linux namespace / seccomp / container / VM 级强隔离；
- 任意第三方代码安全；
- 自动获得新的系统权限；
- 独立第三方安全认证。

原生执行必须显式允许，并使用路径限制、符号链接拒绝、清理环境、临时工作目录、超时和输出上限等约束。

完整边界见 [`docs/NATIVE_INTEROP.md`](docs/NATIVE_INTEROP.md) 和 [`STATUS.md`](STATUS.md)。
