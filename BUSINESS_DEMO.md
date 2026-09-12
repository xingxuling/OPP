# OPP 业务 Demo：旧预约表单接入新 CRM

这个 Demo 用一个很常见的系统集成问题解释 OPP：**旧系统和新系统表达的是同一件事，但字段名字和数据形状不一样。**

场景：

```text
旧预约表单
  name
  phone
  service
  slot
  notes
    ↓
   OPP
    ↓
新 CRM
  customer_name
  phone
  service_code
  preferred_time
  notes
  channel
```

OPP 在这个 Demo 里不会调用真实 CRM，也不会访问外网。它只在本地完成：

1. 调用旧表单模拟 Producer；
2. 用声明式规则把字段转换成 CRM 需要的形状；
3. 调用 CRM 模拟 Consumer；
4. 返回最终结果和一份互操作回执。

## 运行

```bash
python -m pip install -e .
python examples/business_demo.py
```

你会看到类似：

```text
场景：旧预约表单 -> 新 CRM 线索
原始输入：陈小姐 / 物理治疗初诊 / 2026-09-15 14:30
旧系统输出：name / service / slot ...
OPP 转换后：customer_name / service_code / preferred_time ...
新系统结果：accepted = true
状态：PASS
回执根：...
```

## 这个 Demo 说明什么

它说明 OPP 当前已经能把一个具体的 `Producer -> Bridge -> Consumer` 链路真实跑起来，并把转换和结果绑定到回执。

它**不说明**：

- OPP 已经能自动理解任意第三方 CRM；
- 任何字段差异都可以无损转换；
- 当前候选已经是生产级 iPaaS；
- 本地 Demo 等于真实企业系统集成已经完成。

这个 Demo 的意义只是把“用户资料字段怎么从旧系统接到新系统”这件事，从抽象协议变成一个可以直接运行的例子。
