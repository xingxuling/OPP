# OPP Bridge Compiler（OPP 桥编译器）

Bridge Compiler 把已有项目里的 **Protocol / Contract / Interface / Schema / Capability / Evidence / Receipt / Ledger / Bridge（协议 / 契约 / 接口 / 模式 / 能力 / 证据 / 回执 / 账本 / 桥）**候选，通过静态扫描投影到现有 OPP 六协议，而不是发明第七个核心协议。

## 编译链

`Repository snapshot（仓库快照） → bounded static scan（有界静态扫描） → PrimitiveFinding（原语发现） → REP evidence（证据） + RAP artifact（工件） + RCP describe capability（描述能力） → CHP bridge offer（桥握手提议） → Bridge Manifest（桥清单）`

## 为什么 RCP 标为 describe capability（描述能力）

发现 `FOO_PROTOCOL_FORMAT` 只证明某个文件声明了一个候选标识，**不证明源系统真的实现或运行它**。因此生成的 RCP 描述的是“OPP Bridge Compiler 能描述这个候选声明”，而不是伪称“源系统拥有该能力”。所有自动生成能力均 `candidate-only`，`authorityRequired=[]`，且不继承源仓库权限。

## 静态安全边界

- 不 `import` Python，不执行 JS/RCL，不运行被发现的 CLI。
- 默认跳过 `.git`、`node_modules`、build/dist、虚拟环境和缓存目录。
- 单文件、总字节数和文件数都有上限。
- 文档提取只接受“原语关键词 + namespaced id（命名空间标识）”的有界行级提示。
- SHA-256 文件摘要证明扫描对象字节一致性，不证明作者身份或事实真实性。
- Bridge（桥）不执行 Canonical Promotion（规范晋级）。

## CLI（命令行接口）

```bash
opp bridge scan ./some-repo --profile auto
opp bridge compile ./some-repo --profile auto --out ./opp-bridge-output
```

`auto` 目前会尝试识别 `rcl / rncs / dwac / generic` 四个 profile（适配配置）。Profile 只影响发现置信度和系统标签，核心扫描器仍然是通用的。

## 输出

- `manifest.json`：编译清单和权威边界；
- `scan.json`：静态发现；
- `evidence/*.json`：REP 候选证据包；
- `artifacts/*.json`：RAP 候选工件；
- `capabilities/*.json`：RCP “描述能力”；
- `handshake.json`：CHP Bridge Offer（桥握手提议）；
- `validation.json`：所有生成 OPP 信封的结构验证结果。

## 扩展新文明 / 系统

新增系统通常只需在 `opp.bridge.profiles` 增加 profile hints（适配提示）。只有出现新的文件语言或语法形态时，才需要新增 extractor（提取器）。不要为了一个项目复制一套 scanner（扫描器）。
