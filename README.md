# dbk-skills

个人 Agent Skills 集合，沉淀我的开发习惯与工作流。命名统一带 `dbk-` 前缀。

## 分类

| 文件夹 | Skill | 用途 |
|---|---|---|
| `base/` | `dbk-agent-rules` | Agent 协作准则：中文回答、咨询/改动边界、git 操作熔断、命名只推荐 |
| | `dbk-skill-dev` | Agent Skill 全生命周期：创建、修改、迭代、触发优化与评估 |
| `languages/` | `dbk-python-style` | Python 约定：uv、3.10+ 基线、类型注解风格、pathlib、rich/loguru |
| | `dbk-rust-gates` | Rust 门禁：commit 前 fmt+clippy --fix，push 前全量 test |
| `git-workflow/` | `dbk-git-worktree` | worktree 创建流程：分支名建议→确认→`.worktrees/` 落位 |
| | `dbk-upstream-conflict` | 上游合并冲突处理：保留本分支功能、Cargo.lock 重建 |
| | `dbk-pr-feedback` | PR 评审意见处理：先评估→写 notes/review→确认后修复 |

## 安装

使用 [skills CLI](https://github.com/vercel/skills) 安装：

```bash
# 全局安装（所有项目可用）
npx skills add DBinK/dbk-skills -g
```

```bash
# 只装某一个
npx skills add DBinK/dbk-skills --skill dbk-agent-rules -g
```

## 约定

- Skill 格式遵循 [agentskills.io](https://agentskills.io) 规范。
- 触发靠 frontmatter 的 `description` 匹配，新增/修改 skill 后建议跑触发评估（各 skill 的 `evals/trigger-queries.json` 存有正负例查询集）。
- 本地开发时通过 `.agents/skills/` 下的符号链接接入发现路径。
