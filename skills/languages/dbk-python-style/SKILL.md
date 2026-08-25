---
name: dbk-python-style
description: 用户的现代 Python 开发约定，适用于任何涉及 Python 的任务——写代码、改代码、评审、重构、建环境、装依赖、写脚本调试等，只要出现 .py 文件或提到 Python/pip/uv 就应加载本技能，即使用户没有提"规范"或"约定"。包含环境管理（uv）、版本基线（3.10+/3.13+）、类型注解风格、pathlib 文件操作、rich/loguru 调试工具选型等硬性偏好。
license: MIT
compatibility: 需要 uv 与 Python 3.10+（推荐 3.13+）
metadata:
  author: DBinK
  version: "0.1.0"
---

# 现代 Python 开发约定

用户的 Python 编码偏好。写或改 Python 代码时按此执行，不要用与本文冲突的通用写法。

## 环境

- 用 **uv** 管理环境和依赖（建环境、加依赖、跑脚本都用 uv）。
- 版本基线：**偏好 3.13 以上，最低 3.10**；不需要考虑 3.10 之前的兼容性。

## 类型注解

- 对外暴露的函数必须写类型注解；内部函数看情况。
- 3.10+ 基线下**不需要**写 `from __future__ import annotations`。
- 联合类型用 `|`，不用 `typing.Union`：`def f(x: str | None) -> str | int`。
- 不用 `typing.Dict` / `typing.List` 等大写容器，直接用内置小写 `dict` / `list`。
- 抽象容器优先从 `collections.abc` 取，不从 `typing` 取。
- dict 注解可以偷懒不写全内部结构：一般场景写 `dict[str, Any]` 即可；要写细就至少写明 key 类型 `dict[str, object]`。
- 元素意义明确的元组，推荐继承方式创建 namedtuple 类来明确语义。

## 文件操作

- 一律用 **pathlib**，不用 `os.path` 系列。
- 函数签名含路径参数时：类型写 `str | Path`，函数体第一行就转成 `Path` 对象再操作。
- 返回路径时按调用方需求明确二选一：返回 `str` 或返回 `Path`，不要含糊。

## 打印 / 进度 / 日志

- 进度条：简单场景用 `rich.progress.track`，复杂场景（多任务、嵌套、动态刷新）用 `rich.progress.Progress`。
- 打印 json、字典、dataclass 等结构化数据时用：

  ```python
  from rich import print as rprint
  ```

- 需要日志库时用 **loguru**，不用标准库 `logging` 手搭。

## Gotchas

- 新项目初始化时直接按 3.13 基线走，别为了"兼容性"降要求——除非用户明确指定目标版本。
- 改老代码遇到旧式写法（`os.path`、`Union[...]`、logging）时顺手改成上述风格，但大范围重构前先问用户。
