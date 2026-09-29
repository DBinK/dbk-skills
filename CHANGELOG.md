# Changelog

本项目所有显著变更记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，条目按日期组织（个人项目，暂不采用版本号）。

## 2026-09-29

### Changed

- 收敛各技能的 `description`：统一为"做什么 + 何时用 + 不适用"三部分，把原先夹带的流程、规则与机制说明移回正文。涉及 `dbk-upstream-conflict`、`dbk-pr-feedback`、`dbk-rust-gates`、`dbk-git-worktree`、`dbk-doc-style`、`dbk-skill-dev`、`dbk-pr-commit-reply`、`dbk-agent-rules`、`dbk-python-style`。
- `dbk-git-worktree`：修正 description 中的拼写 `swtich` → `switch`。
- `dbk-upstream-conflict`：新增主动调用入口——显式调用且无其他指令时，默认从上游拉取主分支合并进当前分支；description、正文默认流程与触发评估查询同步覆盖该场景。

## 2026-08-25

### Added

- 新增 `dbk-doc-style`：项目文档文风检查与生成（中英文规范、去冗余、读者边界）。
- 新增 `CHANGELOG.md`。

### Changed

- 重写 README：新增核心理念章节（指令分型、熔断、先评估再动手、质量门禁、经验沉淀），补全技能列表并加链接；开头定位改为"供他人直接使用或参考借鉴"。

## 更早

### Added

- 初始版本：`dbk-agent-rules`、`dbk-skill-dev`、`dbk-python-style`、`dbk-rust-gates`、`dbk-git-worktree`、`dbk-upstream-conflict`、`dbk-pr-feedback`。
