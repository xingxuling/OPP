# OPP 的三个现实例子

这些例子用来说明“如果把 OPP 放进真实软件项目，它会处在什么位置”。

它们是**业务映射示例**，不是已经部署完成的客户案例。

## 例子 1：CRM 接入新的预约系统

一家公司原来有 CRM，新做了一个预约系统。

预约系统输出：

```json
{
  "name": "陈小姐",
  "phone": "91234567",
  "booking_time": "2026-09-12T15:00:00"
}
```

CRM 需要：

```json
{
  "customer_name": "string",
  "phone": "string",
  "appointment_at": "string"
}
```

传统做法通常是程序员先读两边文档，再手写一个 adapter。

OPP 更适合先做：

```text
扫描双方接口
  ↓
确认字段和类型
  ↓
判断能否安全映射
  ↓
生成 rename / select 等受限桥接计划
  ↓
明确授权后运行
  ↓
保存回执
```

如果某个字段无法确定，应该报告 `unknown` 或不兼容，而不是猜。

## 例子 2：Agent 接一个新的工具

一个 Agent 找到了一个“创建工单”的工具。

真正接入前，至少要确认：

- 它到底需要什么字段；
- 输出长什么样；
- 当前 Agent 提供的数据是否匹配；
- 是否需要丢字段或补默认值；
- 实际执行时调用了哪个能力。

OPP 可以把这条链拆成：

```text
Agent output
  ↓
能力 / Schema 检查
  ↓
Compatibility
  ↓
Bridge Plan
  ↓
Tool Invocation
  ↓
Receipt
```

这类场景可以和 MCP、A2A 或现有 API 同时存在。OPP 不要求替换它们。

## 例子 3：旧 API 升级，新旧字段不一致

一个内部系统从 API v1 升到 v2。

v1：

```json
{
  "user_id": 123,
  "full_name": "Alice"
}
```

v2：

```json
{
  "id": 123,
  "name": "Alice"
}
```

如果只是字段改名，这类变化适合声明式桥接。

如果 v2 同时改变了业务含义，例如：

```text
full_name 不再等于 name
```

那么 OPP 不应该只因为类型相同就假装它们语义完全兼容。

这也是为什么 OPP 把 `structural`、`lossy`、`unknown` 和 `incompatible` 分开，而不是只有“能/不能”。

## 这三个例子的共同点

OPP 最有价值的地方不是“自动写更多代码”，而是把系统对接里原本散落在程序员脑中的判断显式化：

```text
我知道什么
我不知道什么
哪里兼容
哪里会丢信息
哪里需要人工决定
这次到底执行了什么
```

当系统数量、Agent 数量或集成数量越来越多时，这些判断才开始真正值钱。
