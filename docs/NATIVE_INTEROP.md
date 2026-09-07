# OPP Native Invocation + Interop v0.3（OPP 原生调用与互操作 v0.3）

## 这一层解决什么

v0.2 能证明“项目 A 的输出形状可以通过一个声明式桥变成项目 B 的输入形状”。v0.3 第一次把这条链真正执行：

`Producer invocation（生产端调用） → OPP declarative bridge（OPP 声明式桥） → Consumer invocation（消费端调用） → Interop Receipt（互操作回执）`

## 显式执行原则

静态扫描、Semantic Verify（语义验证）和 Auto Connect（自动连接）仍然**永远不会自动执行扫描到的源码**。

只有同时满足以下条件才进入 Native Invocation（原生调用）：

1. 有显式 `Invocation Spec（调用规范）`；
2. Adapter Kind（适配器类型）是当前允许的 `python-function`；
3. Entry Point（入口）是明确的 `relative/path.py:function_name`；
4. Source Root（源码根）和入口通过路径包含检查；
5. 入口路径没有 symlink（符号链接）；
6. 调用方显式设置 `allow_execution / --allow-execution（允许执行）`；
7. timeout（超时）、输出大小、调用约定等全部在受支持范围内。

## 当前 Python Function Adapter（Python 函数适配器）

父进程不会使用 shell（命令解释器）拼接命令，而是直接使用 argv（参数向量）启动当前 Python 解释器的 `-I` isolated mode（隔离模式），运行 OPP 自有 child runner（子运行器）。

子运行器只接受一个明确 Python 文件和一个顶层函数名，通过 JSON stdin（标准输入）收取参数，通过 JSON stdout（标准输出）返回结果。当前调用约定：

- `kwargs`：JSON object（JSON 对象）展开为关键字参数；
- `single`：整个 JSON 值作为一个参数。

目标函数自己的 stdout / stderr（标准输出 / 标准错误）被捕获并进入调用回执。

## Process Sandbox（进程沙箱）的真实边界

当前是 **bounded child process（有界子进程）**，不是强安全沙箱。已经实现：

- 显式执行同意；
- 无 shell；
- source-root containment（源码根包含检查）；
- symlink 入口拒绝；
- sanitized environment（清理后的环境变量）；
- ephemeral cwd（临时工作目录）；
- timeout（超时）；
- stdout/stderr 输出接受上限；普通 Python 文本输出在 child runner（子运行器）内提前截断/失败；低层文件描述符直接写入仍只由父进程回收后的接受闸门约束；
- 非 JSON 返回失败关闭；
- 无隐藏重试；
- 无权限自动提升。

当前**没有宣称**：Linux namespace、seccomp、容器、虚拟机、网络断开、文件系统完全隔离或恶意代码安全执行。目标代码依然可能主动访问操作系统能力，因此不可信代码应放到更强的外部沙箱中。

## Interop PASS（互操作通过）到底证明什么

`PASS` 只证明这一条具体测试链：

- 指定生产端确实被调用成功；
- 生产端结果确实经过指定 OPP Bridge Plan（桥计划）；
- 转换结果确实传给指定消费端；
- 消费端确实返回 JSON 可验证结果；
- 每一步生成内容根与回执根。

它**不证明**所有输入、所有版本、所有环境都兼容，也不证明业务语义绝对正确。

## 示例

```bash
opp interop run examples/interop-run.json examples/interop-input.json --allow-execution --out interop-result.json
```

如果没有 `--allow-execution（允许执行）`，命令必须失败关闭。
