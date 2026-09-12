# OPP Examples

这个目录分成三类例子。第一次看仓库时，不需要把所有 JSON 都读一遍。

## 1. 先看协议对象

这些文件展示 OPP 核心对象长什么样：

- `capability.json` — 一个系统声明自己会什么；
- `artifact.json` — 描述代码、文档、模型等工件；
- `evidence.json` — 把主张和证据绑定；
- `state.json` — 表达状态、事实、观察和预测；
- `exchange.json` — 跨系统交换对象；
- `handshake-*.json` — 两个系统握手时的声明。

可以直接验证：

```bash
python -m opp validate examples/capability.json
python -m opp validate examples/artifact.json
```

## 2. 再看接口扫描和桥接

- `semantic-fixtures/` — 用来验证 Python / TypeScript / JSON Schema 的接口提取和兼容性判断；
- `bridge-fixtures/` — 用来验证 Bridge Compiler 扫描和编译。

典型命令：

```bash
python -m opp semantic verify ./examples/semantic-fixtures --profile auto
```

真正使用时，把路径换成你自己的仓库即可。

## 3. 最后看真实互操作

- `native-fixtures/` — 最小 Producer / Consumer Python 夹具；
- `invocation-producer.json` — Producer 调用规范；
- `invocation-consumer.json` — Consumer 调用规范；
- `interop-input.json` — 输入数据；
- `interop-run.json` — 完整互操作运行描述。

运行：

```bash
opp interop run examples/interop-run.json examples/interop-input.json \
  --allow-execution \
  --out interop-result.json
```

这一步会进入显式原生执行，所以必须提供 `--allow-execution`。

## 推荐阅读顺序

```text
capability.json
    ↓
semantic-fixtures/
    ↓
bridge-fixtures/
    ↓
interop-run.json
    ↓
interop-result.json
```

如果只是想知道 OPP 是否适合你的项目，先看 [`../docs/USE_CASES.md`](../docs/USE_CASES.md)。
