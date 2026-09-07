# OPP Auto Connect（OPP 自动连接）

`opp semantic connect A B` 接受两个源码目录，分别静态生成 Semantic Report（语义报告），然后搜索：

`A.interface.output -> OPP Transform Plan -> B.interface.invocation-input`

## 搜索原则

1. 只比较存在静态形状证据的端口；
2. 先做廉价类型/字段预筛选，避免大型仓库出现无界 O(n×m)（平方级）爆炸；
3. `maxPairs` 对真实比较次数设硬上限；
4. 默认只保留 `exact / structural`（精确 / 结构兼容）桥；
5. `lossy`（有损）必须显式允许；
6. `unknown / incompatible`（未知 / 不兼容）不会生成可执行候选桥；
7. 自动连接不会执行 A 或 B 的源码。

## 当前执行边界

Auto Connect 当前完成的是**数据表示桥**，不是完整 native invocation adapter（原生调用适配器）。要真正让两个进程/库互调，下一层仍需：

- native invocation adapter（原生调用适配器）；
- transport binding（传输绑定）；
- runtime sandbox（运行时沙箱）；
- interoperability test（互操作测试）；
- receipt / evidence（回执 / 证据）闭环。

这层边界是刻意保留的：OPP 可以自动证明“数据形状存在可审计转换”，但不会把这一步冒充成“两个项目已经真实互操作”。
