# dbk-skills

[![skills.sh](https://skills.sh/b/DBinK/dbk-skills)](https://skills.sh/DBinK/dbk-skills)
[![Specification](https://img.shields.io/badge/spec-agentskills.io-black)](https://agentskills.io)
[![License: MIT](https://img.shields.io/github/license/DBinK/dbk-skills)](LICENSE)

与 Agent 协作开发时，失控往往发生在边界模糊的瞬间：咨询类问题被当成改动执行、修改完成后未经确认便自动 `commit` 与 `push`、外部评审意见未经甄别就全盘采纳。

`dbk-skills` 是一套面向代码质量与工程安全的 Agent Skills 规则集。核心逻辑只有一条：**明确人机权责边界，不可逆操作必须显式授权**。

如果你同样看重代码架构与工程交付质量，希望建立受控、可预测的人机协作流程，这套 Skills 可以提供直接支持。

## 痛点根源：过度顺从与行动偏向

问题的根源在于大模型的后训练机制（SFT/RLHF）：为了追求高效的任务达成率与人机对齐，模型被强化出了强烈的**过度顺从与行动偏向（Action Bias）**。这导致 Agent 在面对外部输入时，天生倾向于直接推进并执行操作，容易跳过对指令性质与权责边界的审视。常见问题集中在四个环节：

| 痛点 | 表现 |
|---|---|
| 越权执行 | 未经授权 `git commit`，咨询类请求被当成改动类处理 |
| 盲从外部输入 | 照单采纳 PR 评审意见、上游变更、自动修复结果，不核实真伪与价值 |
| 质量门禁缺失 | 格式化、lint、测试依赖自觉，缺陷代码进入版本历史 |
| 经验不沉淀 | 纠错结论停留在单次会话，同类错误跨会话复现 |

## 设计原则

所有 Skill 遵循同一核心原则：**人是决策者，Agent 是执行者**，并以此约束各协作环节：

- **指令分型**：咨询类只分析不改文件，改动类只改文件。
- **不可逆动作熔断**：`commit` / `push` / 删除等写操作等用户显式授权。
- **先评估再动手**：评审意见、上游变更、自动修复结果先核实真实性，再判断修复价值。
- **质量门禁前置**：commit 前格式化 + lint 自动修复，push 前按分支相对 main 的变更执行受影响测试。
- **经验持续沉淀**：每次纠错回写到对应技能的注意事项。

## Skills

| 分类 | Skill | 用途 |
|---|---|---|
| `base/` | [`dbk-agent-rules`](skills/base/dbk-agent-rules/) | Agent 协作准则：中文回答、咨询/改动边界、git 操作熔断、命名只推荐 |
| | [`dbk-skill-dev`](skills/base/dbk-skill-dev/) | Skill 全生命周期开发：创建、迭代、触发优化与评估 |
| | [`dbk-doc-style`](skills/base/dbk-doc-style/) | 项目文档文风检查与生成：中英文规范、去冗余、读者边界 |
| `languages/` | [`dbk-python-style`](skills/languages/dbk-python-style/) | Python 约定：uv、3.10+ 基线、类型注解风格、pathlib、rich/loguru |
| | [`dbk-rust-gates`](skills/languages/dbk-rust-gates/) | Rust 门禁：commit 前 fmt + clippy --fix，push 前最小受影响 test，影响不明时扩大范围 |
| `git-workflow/` | [`dbk-git-worktree`](skills/git-workflow/dbk-git-worktree/) | worktree 创建流程：分支名建议 → 确认 → `.worktrees/` 落位 |
| | [`dbk-upstream-conflict`](skills/git-workflow/dbk-upstream-conflict/) | 上游合并：主动拉取上游主分支合并到当前分支。冲突处理保留本分支功能、Cargo.lock 重建 |
| | [`dbk-pr-feedback`](skills/git-workflow/dbk-pr-feedback/) | 评审意见评估（默认本分支 PR 未处理意见，支持指定 PR 或上下文意见）：逐条核实 → 写 `notes/review`（输出绝对路径）→ 定夺后分流 |
| | [`dbk-pr-commit-reply`](skills/git-workflow/dbk-pr-commit-reply/) | PR 评审收尾（作者视角，仅手动触发）：按领域拆提交 → push → 逐条回复评审意见 → 重新请求评审 |
| | [`dbk-pr-execute-reply`](skills/git-workflow/dbk-pr-execute-reply/) | PR 评审执行落地（作者视角，仅手动触发）：执行已定方案 → 分段提交 → push → 逐条回复评审意见 → 重新请求评审 |
| | [`dbk-pr-submit-review`](skills/git-workflow/dbk-pr-submit-review/) | PR 评审意见提交（Reviewer 视角，仅手动触发）：筛选评估笔记条目 → 重新编号 → 按原格式批量发到 PR 内联评论 |

## 安装

全局安装（所有项目可用）：

```bash
npx skills add DBinK/dbk-skills -g -y
```

只装某一个：

```bash
npx skills add DBinK/dbk-skills --skill dbk-agent-rules -g
```

## 约定

- Skill 格式遵循 [agentskills.io](https://agentskills.io) 规范，统一带 `dbk-` 前缀。
- 触发靠 frontmatter 的 `description` 匹配，新增或修改技能后需跑触发评估（正负例查询集在各技能 `evals/trigger-queries.json`）。
- 本地开发时通过 `.agents/skills/` 下的符号链接接入，改动即时生效。
