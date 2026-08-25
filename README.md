# dbk-skills

我是对代码掌控欲很强的人，和 Agent 协作得多了，经常会遇到这样的情况：让 Agent 改代码，改完了它竟然没经我审批，就自己 commit 还 push 了。无论什么模型，都经常做出类似这样预期之外的行动，我需要经常在协作时提醒它。

一来二去也提醒得烦了，于是我把需要反复提醒它的场景，沉淀成现在这一套 Skills。它做的事很单一，把边界讲清楚，让 Agent 动手前先确认。如果你也看重代码架构和质量，不喜欢 Agent 乱改，这套 Skills 应该对你有用。

## 为什么 Agent 不听话

我认为根源是 LLM 的**指令遵循倾向**：外部输入进来，它倾向直接执行，不做判断。问题集中在四个环节：

| 痛点 | 表现 |
|---|---|
| 越权执行 | 未经授权 `git commit`，咨询类请求被当成改动类处理 |
| 盲从外部输入 | 照单采纳 PR 评审意见、上游变更、自动修复结果，不核实真伪与价值 |
| 质量门禁缺失 | 格式化、lint、测试依赖自觉，缺陷代码进入版本历史 |
| 经验不沉淀 | 纠错结论停留在单次会话，同类错误跨会话复现 |

## 设计原则

针对上述痛点，我做了下面的设计：

所有 Skill 遵守同一原则：**人是决策者，Agent 是执行者**。落到下面的规则，分别约束上面的每个环节：

- **指令分型**：咨询类只分析不改文件，改动类只改文件。
- **不可逆动作熔断**：`commit` / `push` / 删除等写操作等用户显式授权。
- **先评估再动手**：评审意见、上游变更、自动修复结果先核实真实性，再判断修复价值。
- **质量门禁前置**：commit 前格式化 + lint 自动修复，push 前全量测试。
- **经验持续沉淀**：每次纠错回写到对应技能的 Gotchas。

## Skills

| 分类 | Skill | 用途 |
|---|---|---|
| `base/` | [`dbk-agent-rules`](skills/base/dbk-agent-rules/) | Agent 协作准则：中文回答、咨询/改动边界、git 操作熔断、命名只推荐 |
| | [`dbk-skill-dev`](skills/base/dbk-skill-dev/) | Skill 全生命周期开发：创建、迭代、触发优化与评估 |
| | [`dbk-doc-style`](skills/base/dbk-doc-style/) | 项目文档文风检查与生成：中英文规范、去冗余、读者边界 |
| `languages/` | [`dbk-python-style`](skills/languages/dbk-python-style/) | Python 约定：uv、3.10+ 基线、类型注解风格、pathlib、rich/loguru |
| | [`dbk-rust-gates`](skills/languages/dbk-rust-gates/) | Rust 门禁：commit 前 fmt + clippy --fix，push 前全量 test |
| `git-workflow/` | [`dbk-git-worktree`](skills/git-workflow/dbk-git-worktree/) | worktree 创建流程：分支名建议 → 确认 → `.worktrees/` 落位 |
| | [`dbk-upstream-conflict`](skills/git-workflow/dbk-upstream-conflict/) | 上游合并冲突处理：保留本分支功能、Cargo.lock 重建 |
| | [`dbk-pr-feedback`](skills/git-workflow/dbk-pr-feedback/) | PR 评审意见处理：先评估 → 写 notes/review → 确认后修复 |

## 安装

全局安装（所有项目可用）：

```bash
npx skills add DBinK/dbk-skills -g
```

只装某一个：

```bash
npx skills add DBinK/dbk-skills --skill dbk-agent-rules -g
```

## 约定

- Skill 格式遵循 [agentskills.io](https://agentskills.io) 规范，统一带 `dbk-` 前缀。
- 触发靠 frontmatter 的 `description` 匹配；新增或修改技能后跑触发评估（各技能的 `evals/trigger-queries.json` 存有正负例查询集）。
- 本地开发时通过 `.agents/skills/` 下的符号链接接入发现路径，改动能即时生效。
