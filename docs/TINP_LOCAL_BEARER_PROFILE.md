# OPP × TINP 本地承载绑定规范 v0.1

## 裁决

OPP 不新增 Wi-Fi 协议，也不拥有 socket、网卡、路由或 Mesh（网状网络）驱动。

- OPP 继续回答：**交换什么对象/能力、双方同意什么语义、结果证据是什么。**
- TINP 继续回答：**节点在哪里、走哪条路径、使用哪个 transport/bearer（传输/承载）、怎样发现和转发。**
- RCL 继续回答：**这条候选承载是否允许被提交。**

因此“OPP 自己使用 Wi-Fi”的正确实现不是把 Wi-Fi 代码塞进 OPP，而是：

```text
OPP Reality Envelope / CHP / RCP
        ↓
TINP OPP profile / capability route
        ↓
TINP local-first bearer
        ↓
Wi-Fi LAN / Ethernet LAN / 已建好的 Wi-Fi Direct / Hotspot
```

## 绑定规则

OPP envelope（现实信封）可以在 `extensions.transportEvidence` 中携带**观察性传输证据**，但该字段不得创建、扩大或替代 authority（权限）。

建议最小形态：

```json
{
  "extensions": {
    "transportEvidence": {
      "protocol": "taowind.tinp.v0.2",
      "bearerProfile": "tinp.local-first.v0.1",
      "scope": "local-lan",
      "metered": false,
      "publicEgress": false,
      "routeReceiptRef": "..."
    }
  }
}
```

这些值只表示 TINP 提供的可审计观察。OPP CHP/RCP 的权限、能力和证据要求仍按 OPP 自己的规则判断。

## 安全边界

1. `LAN discovered`（局域网发现到）不等于 `identity trusted`（身份可信）。
2. `CHP accepted`（握手接受）不等于 `authority granted`（权限已经授予）。
3. `local-lan`（本地局域网）不等于 `confidential`（内容保密）；需要保密时仍应使用 TLS、加密 payload 或受信链路。
4. `metered=false`（非计费）只表示该候选被 TINP 视作本地直连路径，不代表任何 ISP/运营商公网服务免费。
5. OPP 不得根据 Wi-Fi SSID、MAC、IP 或 multicast advertisement（组播公告）单独创建主体身份或权限。

## 当前实现对应

TINP 候选分支 `codex/tinp-local-bearer-v01` 新增：

- local-first bearer policy（本地优先承载策略）；
- RCL bearer admission（RCL 承载准入）；
- 非回环 LAN TINP transport（局域网传输）；
- 签名 LAN discovery（局域网发现）；
- unknown peer（未知节点）不自动进入 trust set（信任集合）。

OPP 无需复制上述实现；现有 TINP→OPP CHP projection（投影）和 OPP Reality Envelope extension（扩展字段）足够承载本轮绑定。

## 验证状态

`SEMANTIC_BINDING_DEFINED / PHYSICAL_WIFI_PENDING`

TINP 本地定向测试已验证非回环私网 socket 与 RCL/安全边界；OPP 本轮不修改执行语义，因此没有把 TINP 测试冒充成 OPP 全仓回归。
