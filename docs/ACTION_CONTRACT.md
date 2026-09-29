# OPP Action Contract v0.1

OPP Action Contract 是 Agent Action Trust Plane（智能体行动信任平面）里的**语义合同层**。

它把一份已经通过 OPP RCP 验证的 capability（能力声明）和一次具体行动压成一个可复核的 rooted contract（带内容根的行动合同），交给 TINP 或其他 authority plane（权限平面）决定是否允许执行。

## 不做什么

Action Contract **不授予权限**、不认证主体、不执行代码，也不声称提供操作系统级沙箱。

固定字段 authorityGranted 必须为 false。

## 当前有界副作用词汇

v0.1 只接受四种副作用：

- filesystem.write：文件系统写入；
- network.egress：网络外连；
- credential.read：凭据读取；
- process.spawn：启动进程。

未知副作用默认拒绝，而不是降级成“其他”。

每个副作用都必须同时声明具体 resource，例如：

    {"kind":"filesystem.write","resource":"workspace:/project/src/app.js"}

OPP 只绑定这个资源标识，不负责把它解释成真实 OS 权限；真正的资源边界由 TINP lease（权限租约）和执行 Provider 负责。

## 生成链

    RCP capability
    + subject
    + concrete action input
    + requested side effects
            ↓
    build_action_contract()
            ↓
    OPP Action Contract
            ↓
    TINP signed lease + RCL admission

Action Contract 绑定：

- 完整 capability 及 capabilityRoot；
- subjectId；
- capabilityId / operation；
- authorityRequired；
- requestedEffects；
- reversibility；
- riskClass；
- actionInputRoot；
- contractRoot。

riskClass 只是由已声明副作用和可逆性确定的描述字段，不是授权依据。当前 credential.read、process.spawn 或不可逆动作标为 high。

## Prompt injection 边界

Prompt / README / 网页文本只进入 actionInput，最终被绑定成 actionInputRoot。

它不能靠文本内容自行增加 credential.read、network.egress、process.spawn 或更大的 filesystem.write 范围。

如果请求的副作用没有出现在 RCP sideEffects 中，合同生成直接 fail closed（失败关闭）。

## Python 示例

    from opp.sdk import build_action_contract

    contract = build_action_contract(
        capability,
        subject_id="agent:coder",
        requested_effects=[
            {
                "kind": "filesystem.write",
                "resource": "workspace:/project/src/app.js",
            }
        ],
        action_input={"prompt": "patch app.js"},
    )

完整可运行例子见 examples/agent_action_contract.py。

## 验证边界

verify_action_contract() 不只重算 contractRoot，还重新核对：

- capability root；
- capability / operation 绑定；
- authority 列表；
- effect 排序和重复；
- effect 是否真的由 RCP 声明；
- reversibility；
- risk class；
- authorityGranted == false。

这避免“攻击者重算一个合法 hash 就能修改语义”的假完整性。

## 与 TINP 的边界

OPP 回答：

> 这次动作是什么、需要什么能力、会碰什么资源、有什么副作用？

TINP 回答：

> 当前主体是否真的拿到了这些权限、在哪个 Provider 上执行、失败后是什么状态、结果与副作用是否可以接受？

两边故意不互相吞并 owner。
