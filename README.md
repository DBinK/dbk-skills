# dbk-skills

个人 Agent Skills 集合。我把自己的开发习惯与工作流沉淀为 Agent 可执行的规则，供他人直接使用或参考借鉴：通过 [skills CLI](https://github.com/vercel/skills) 安装到任何支持 [Agent Skills](https://agentskills.io) 规范的客户端，Agent 就能按这套规则协作开发。

## 核心理念

这些技能共同表达一个原则：**人是决策者，Agent 是执行者**。

1. **指令分型**：咨询类（"看看""评估下"）只分析不改文件；改动类只改文件。
2. **不可逆动作熔断**：add / commit / push / 删除等会产生历史记录或不可逆后果的动作，一律等用户明确要求才做。
3. **先评估再动手**：上游变更、评审意见、自动修复的结果都不盲从——先核实是否属实，再判断修复价值。
4. **质量门禁前置**：commit 前格式化 + lint 自动修复，push 前全量测试；不带病提交。
5. **经验持续沉淀**：每次纠错都回写到对应技能的 Gotchas，同类错误不犯第二次。

## 技能列表

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

```bash
# 全局安装（所有项目可用）
npx skills add DBinK/dbk-skills -g
```

```bash
# 只装某一个
npx skills add DBinK/dbk-skills --skill dbk-agent-rules -g
```

## 约定

- Skill 格式遵循 [agentskills.io](https://agentskills.io) 规范，统一带 `dbk-` 前缀。
- 触发靠 frontmatter 的 `description` 匹配；新增或修改技能后跑触发评估（各技能的 `evals/trigger-queries.json` 存有正负例查询集）。
- 本地开发时通过 `.agents/skills/` 下的符号链接接入发现路径，改动能即时生效。
