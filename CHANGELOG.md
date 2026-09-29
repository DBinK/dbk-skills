# Changelog

本项目所有显著变更记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，条目按日期组织（个人项目，暂不采用版本号）。

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
- `dbk-skill-dev`：触发实测脚本（`scripts/run_trigger_eval.py`）要求 Python 3.10+——加 PEP 723 元数据与解释器版本守卫，调用方式统一为 `uv run`，AGENTS.md 与技能正文同步更新。

## 2026-08-25

### Added

- 新增 `dbk-doc-style`：项目文档文风检查与生成（中英文规范、去冗余、读者边界）。
- 新增 `CHANGELOG.md`。

### Changed

- 重写 README：新增核心理念章节（指令分型、熔断、先评估再动手、质量门禁、经验沉淀），补全技能列表并加链接；开头定位改为"供他人直接使用或参考借鉴"。

## 更早

### Added

- 初始版本：`dbk-agent-rules`、`dbk-skill-dev`、`dbk-python-style`、`dbk-rust-gates`、`dbk-git-worktree`、`dbk-upstream-conflict`、`dbk-pr-feedback`。
