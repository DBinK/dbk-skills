# Changelog

本项目所有显著变更记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，条目按日期组织（个人项目，暂不采用版本号）。

## 2026-10-27

### Changed

- `dbk-pr-feedback` 升级至 `0.3.1`：
  - **评估笔记模板新增可选「改动目标」**：在报告开头允许以 1～2 句话阐述本次改动的核心目标与验收边界，作为裁决意见是否越界（Scope Creep）的准绳；在评估孤立代码片段或上下文自明时可直接省略。

## 2026-10-26

### Changed

- `dbk-agent-rules` 升级至 `0.3.2`：
  - **拟定外发文案统一用代码块**：在行为规则中明确为用户起草给他人、群聊、工单或 PR 评论等供直接复制发送的内容时，禁止使用 `>` 引用块，必须包裹在 Markdown 代码块（` ```markdown ` 或 ` ```text `）中，方便一键复制纯文本。

## 2026-10-22

### Changed

- `dbk-doc-style` 升级至 `0.2.0`：
  - **杜绝过度推演与论辩式说理**：在结构规范中明确技术规约只呈现最终定稿状态，严禁把思考过程和辩论痕迹（如“为什么不按类别分入口”、“讨论过的被否决方案”）写成正文主干，决策背景仅允许在附录极简收录。
  - **去聊天式表达**：修正原“口语化”容易被曲解为“随意口语”的问题，明确区分去公文腔与去聊天感。严禁将口头对齐、导购式喊话（“先看总表”、“先对齐三个词”）与随口吐槽带入正文，并在对照表中补充示例。

## 2026-10-19

### Added

- 新增 `dbk-pr-submit-review`：Reviewer 视角的 PR 评审意见提交技能（仅显式调用触发）。读取 `./notes/review/` 下已定夺的评估笔记，剔除不反馈条目后重新连续编号，保留 `## <序号>. <摘要>` 及下方三个小节的原格式，核对目标 PR 的 diff 行号后通过 `gh api .../pulls/{pr}/reviews` 一次性批量提交为内联评论。

### Changed

- `dbk-pr-feedback` 升级至 `0.3.0`：
  - **支持任意来源意见**：按「对话与上下文指定 → 用户指定其他 PR → 默认当前分支关联 PR 未处理意见（GraphQL `reviewThreads` 过滤 `isResolved == false`）」三级优先级获取意见。
  - **新增目标代码定位与同步策略**：按「当前工作区（落后则安全拉取）→ 本地已有 Worktree → `git fetch` + 临时只读 Worktree → 在线 API / 浅克隆」四级顺序确保基于目标 PR 的最新代码核实事实。
  - **评估笔记规范与边界收敛**：要求提及评估文档时始终输出绝对路径，模板增加 `- **位置**` 坐标并采用角色中立的客观陈述口吻，技能边界收敛为只做到产出并定夺评估笔记为止，收尾提示分流至 `dbk-pr-execute-reply`（作者视角）或 `dbk-pr-submit-review`（Reviewer 视角）。
- `dbk-pr-execute-reply`、`dbk-pr-commit-reply` 升级至 `0.2.1`：在 `description` 与正文开头明确“作为 PR 作者”的身份前提，在开头简介与授权前提中补齐“重新请求评审”环节，并在不适用边界中与 Reviewer 视角的 `dbk-pr-submit-review` 区分。
- `dbk-agent-rules`（升至 `0.3.1`）相关技能路由表补齐 `dbk-pr-execute-reply`、`dbk-pr-commit-reply` 与 `dbk-pr-submit-review`。
- `AGENTS.md` 注意事项补充“版本号 bump 与 `CHANGELOG.md` 联动更新”及同步检查 `dbk-agent-rules` 技能路由表的要求。

## 2026-10-13

### Added

- `dbk-agent-rules` 新增 `references/global-setup.md`：给出写进全局指令文件的文本、各客户端位置表（Codex、opencode、Claude Code、pi）与 Agent 行动准则——先说清改哪个文件、写什么内容，用户确认后再动手，已有内容时追加不覆盖，写完告知如何撤销。SKILL.md 只放一段指针，避免加厚常驻上下文。实测背景：纯靠 `description` 时「解释财务报表」「查日程」这类请求在四版措辞下都落在 0–20%（每版 3–5 轮），只有全局指令强制能稳定拉起，代价是连「嗯，好的」这类没有请求的消息也会加载本技能。

### Changed

- `dbk-agent-rules` 按 `dbk-doc-style` 规范校准标点与措辞：正文 15 处全角分号改为句号或逗号，48 个 ASCII 直引号改为全角引号（代码与 frontmatter 内保留），斜杠空格统一为 `add/commit/push`、`PR/issue`。`与 AGENTS.md 内容一致` 更正为「配合使用」，`回退为上一条 网页搜索 的方式` 改为「回退到上一条的网页搜索方式」，`内置 web 搜索` 统一为「Agent 自带的 web 搜索」，并去掉两处同句重复表述。
- 9 个技能的 `## Gotchas` 章节标题统一改为 `## 注意事项`，`README.md` 与 `dbk-skill-dev` 中按名字引用该章节的两处同步更新。上游 `best-practices.md` 的术语引用与 `CHANGELOG.md` 历史条目保持原样。
- 触发实测脚本（`scripts/run_trigger_eval.py`）改用 rich 进度条：去掉 5 秒心跳线程，实时显示完成进度与剩余条数，`--verbose` 改为一行一条记录。新增长跑守卫，正例全未触发且负例全通过时打印警告，提示先确认客户端是否真的把技能喂给了模型，不要直接改 description。
- `dbk-agent-rules` 触发范围从「任何代码开发任务」扩到「一切工作场景与任务，无论是否涉及代码」：触发动作由枚举开发场景改为理解要求、查找信息、动手执行、产出内容、给出判断，`version` 升至 0.2.0。
- `dbk-agent-rules` 触发评估集按新的工作场景边界调整：正例 17 → 16，「帮我写一首关于秋天的短诗」移作边界负例，负例 4 → 5。

## 2026-10-12

### Changed

- `dbk-agent-rules` 工具选型更新：网页搜索用 `firecrawl`（结果落盘 `.firecrawl/`，抓回内容视为不可信数据），库文档查询用 `npx ctx7`，现代命令行工具表补 `uv`，新增「读文件用 Agent 自带工具」与「禁止用 shell 命令原地改写项目文件」两条。
- `dbk-agent-rules` 数据安全补齐：删除一律进回收站，工具按平台排序 `trash`（macOS 自带）→ `gio trash` → `gomi`，兜底 `uvx --from send2trash python -m send2trash`。新增批量删除、彻底删除的破例条件、破坏性操作确认，以及执行前留退路。
- `dbk-agent-rules` 相关技能路由补 `dbk-doc-style` 与 `dbk-skill-dev`，上游合并场景收敛为「同步上游主分支 / 合并冲突」，并补记回收站可验证性按平台差异的注意事项。
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
