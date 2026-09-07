# RCL bridge note（RCL 桥说明）

`opp_native_interop_v0.3.rcl` 只表达 OPP v0.3 的 host capability（宿主能力）、warrant（权限许可）、candidate boundary（候选边界）和“不得宣称强 OS 沙箱”的证据约束。

实际 Python 子进程创建属于 Host Runtime（宿主运行时）能力，目前由 OPP Python reference runtime（Python 参考运行时）实现；本文件不宣称 RCL Core（RCL 核心）已经原生获得任意进程生成能力，也没有修改 RCL Canonical（规范核心）所有权。
