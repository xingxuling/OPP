# Integration Court｜OPP × TINP Local Bearer Profile

## 目标裁决

PASS / BOUNDED（通过 / 有边界）。

正确集成方式是让 TINP 拥有 Wi-Fi/LAN 承载，OPP 只消费 TINP 的传输证据与既有能力协商结果；禁止在 OPP 内复制 socket、peer discovery（节点发现）或 route authority（路由权限）语义。

## 影响模块

- 新增 `docs/TINP_LOCAL_BEARER_PROFILE.md`
- 新增 `examples/tinp-local-bearer-evidence.json`
- 本文件

OPP 运行时代码、CHP、RCP、CHA、Reality Envelope schema（现实信封模式）均未修改。

## 验收标准

- 文档明确 Canonical Owner（唯一权威所有者）边界。
- 示例只把 transport evidence（传输证据）放在 extension（扩展）层，不创建权限。
- 不把 LAN/Wi-Fi 发现当身份认证。
- 不把本地直连解释成免费公网。

## 测试/证据

本轮 OPP 没有运行时代码变更，因此不伪造“OPP 新测试通过”。对应 transport/RCL/security（传输/RCL/安全）执行证据来自同日 TINP local-first bearer 候选的 9/9 定向测试；OPP 只冻结集成契约。

## 下一步

真实两设备 Wi-Fi 验证后，可把 TINP route receipt（路由回执）引用接入 OPP REP/CHA session evidence（证据）链；在此之前状态保持 `SEMANTIC_BINDING_DEFINED / PHYSICAL_WIFI_PENDING`。
