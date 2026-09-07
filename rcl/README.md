# RCL Bridge Candidate（RCL 桥候选）

`opp_protocol_suite.rcl` 使用 RCL（Reality Compiler Language，现实编译语言）已公开示例中的 `reality / meta / host / quantitative / reflect` 结构表达 OPP 的三条核心语义：

1. 协议注册表是可反思的 Meta（元）对象；
2. `validate / seal / negotiate`（验证 / 封装 / 协商）是 Host（宿主）提供的能力面，而不是自动权威；
3. 验证证据必须带 uncertainty / confidence / evidence / calibrated-by（不确定度 / 置信度 / 证据 / 校准来源）。

当前仓库没有把 RCL 编译器 vendored（内嵌复制）进来，因此本文件状态为 **RCL-SYNTAX-CANDIDATE（RCL 语法候选）**。JSON Schema 与 Python 参考运行时是本版本已本地执行验证的部分。
