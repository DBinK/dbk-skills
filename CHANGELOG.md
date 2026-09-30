# Changelog

本项目所有显著变更记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，条目按日期组织（个人项目，暂不采用版本号）。

## 2026-09-30

### Changed

- 校验工具用法改为优先 `uvx skills-ref`（免安装、每次按最新版解析，可选 `--refresh` 强制刷新），`uv tool install` 退为固定版本/离线备选；同时写明"不带子命令退出码 2"是用法提示而非安装失败。核实后补记两条坑：PyPI 元数据里的仓库链接（`anthropics/agentskills`）已 404，公开仓库为 `agentskills/agentskills`；且 PyPI 版本（0.1.1）领先仓库 main（0.1.0），不要假设源码形式更新。AGENTS.md 与 `dbk-skill-dev` 同步。
- 触发实测脚本补可观测性：开跑前打印规模与预检耗时，运行中每 5 秒打一次心跳（完成数 + 正在跑的序号及已耗时），`--verbose` 每完成一次运行输出一行，结尾汇总每条查询的平均耗时与整批总耗时、最慢单次。

## 2026-09-29

### Added

- 为 `dbk-agent-rules`、`dbk-skill-dev`、`dbk-python-style` 补充 `evals/trigger-queries.json`，触发评估覆盖全部 10 个技能。

### Changed

- 复测触发率后调整 3 条 description 的触发语与"不适用"边界：`dbk-doc-style` 补"文档写得怎么样"一类问法，`dbk-git-worktree`、`dbk-upstream-conflict` 补误触发场景。

- 收敛 8 个技能的 `description`：统一为"做什么 + 何时用 + 不适用"，把原先夹带的流程、规则与机制说明移回正文，并补上"不适用"边界。涉及 `dbk-upstream-conflict`、`dbk-pr-feedback`、`dbk-rust-gates`、`dbk-git-worktree`、`dbk-skill-dev`、`dbk-pr-commit-reply`、`dbk-agent-rules`、`dbk-python-style`。
- `dbk-pr-commit-reply`、`dbk-pr-execute-reply`：逐条回复评审意见后新增"重新请求评审"步骤——用 `gh api` 把留下意见的人类 reviewer 重新加回评审请求，汇报与 Gotchas 同步补充机器人跳过、重复请求等要点。
- `dbk-git-worktree`：修正 description 中的拼写 `swtich` → `switch`。
- `dbk-upstream-conflict`：新增主动调用入口——显式调用且无其他指令时，默认从上游拉取主分支合并进当前分支；description、正文默认流程与触发评估查询同步覆盖该场景。
- `dbk-doc-style`：中文正文不用分号 `；` 的规则覆盖全部用法——连接并列分句与分隔句内并列成分都在内，附并列成分改顿号的例子；检查清单的改写方式同步对齐。
- `dbk-skill-dev`：触发实测脚本（`scripts/run_trigger_eval.py`）要求 Python 3.10+——加 PEP 723 元数据与解释器版本守卫，调用方式统一为 `uv run`，去掉 3.9 兼容写法；AGENTS.md 与技能正文同步更新。
- 触发实测的"整批全 0"补充实测结论：先查客户端自身报错（遇到过 provider 返回 402 额度不足），不要先怀疑 description；脚本 docstring 与 `dbk-skill-dev` 正文同步更正。

## 2026-08-25

### Added

- 新增 `dbk-doc-style`：项目文档文风检查与生成（中英文规范、去冗余、读者边界）。
- 新增 `CHANGELOG.md`。

### Changed

- 重写 README：新增核心理念章节（指令分型、熔断、先评估再动手、质量门禁、经验沉淀），补全技能列表并加链接；开头定位改为"供他人直接使用或参考借鉴"。

## 更早

### Added

- 初始版本：`dbk-agent-rules`、`dbk-skill-dev`、`dbk-python-style`、`dbk-rust-gates`、`dbk-git-worktree`、`dbk-upstream-conflict`、`dbk-pr-feedback`。
