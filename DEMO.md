# 3 分钟看懂 OPP

这份演示不要求你先理解 OPP 的全部协议。

目标只有一个：**看清楚 OPP 如何先检查接口，再在明确授权后跑一条真实的 Producer -> Bridge -> Consumer 链路。**

## 1. 安装

要求 Python 3.10+。

```bash
python -m pip install -e .
```

## 2. 先只扫描，不执行代码

```bash
python -m opp semantic verify examples/semantic-fixtures --profile generic
```

你会看到 OPP 从 Python、TypeScript 和 JSON Schema 中提取出来的接口信息。

这一步只读源码结构，不执行目标仓库代码。

## 3. 跑一条真实互操作链

仓库已经准备了一套最小 Producer / Consumer 夹具：

```text
examples/native-fixtures/producer.py
        |
        | output
        v
   declarative bridge
        |
        v
examples/native-fixtures/consumer.py
```

执行：

```bash
python -m opp interop run examples/interop-run.json examples/interop-input.json \
  --allow-execution \
  --out interop-result.json
```

`--allow-execution` 是故意要求你显式写出来的。没有它，OPP 不会进入原生调用。

成功后重点看 `interop-result.json` 里的：

- Producer 实际输出；
- 使用了什么声明式转换；
- Consumer 实际接收到什么；
- 最终状态；
- receipt（回执）及对应根。

## 4. 为什么这件事有用

现实里的系统对接通常卡在三类问题：

```text
字段不一样
接口契约不一样
出了问题以后不知道当时到底发生了什么
```

OPP 想把这三类问题拆开处理：

```text
先扫描
  ↓
再判断兼容性
  ↓
只生成受限转换
  ↓
明确授权后才执行
  ↓
最后留下回执
```

## 5. 这份 Demo 没证明什么

这个演示只证明仓库里的这条具体夹具可以在当前候选运行时中完成互操作。

它不证明：

- 任意两个第三方项目都能自动连接；
- 当前运行时已经是强安全沙箱；
- OPP 已经成为外部标准；
- 一次本机 PASS 等于生产环境安全。

完整边界见 [`STATUS.md`](STATUS.md) 和 [`docs/NATIVE_INTEROP.md`](docs/NATIVE_INTEROP.md)。

## 下一步

如果你已经看懂这条链，再看：

- [`docs/USE_CASES.md`](docs/USE_CASES.md)：什么时候值得用 OPP；
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：各模块怎么分工；
- [`docs/REAL_WORLD_EXAMPLES.md`](docs/REAL_WORLD_EXAMPLES.md)：三个现实业务映射例子。
