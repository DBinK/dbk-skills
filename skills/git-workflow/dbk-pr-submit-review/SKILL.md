---
name: dbk-pr-submit-review
description: 作为 reviewer 将已定夺的评估笔记（notes/review/）中的评审意见按原格式批量发送为 GitHub PR 的内联评论（inline review comments）。仅在用户显式调用时使用（点名 dbk-pr-submit-review，或明确要求"把评估意见发到 PR 内联评论""提交 review 评论给提 PR 的人"）；不要从上下文自动触发。只评估意见不发评论、作为 PR 作者改代码并回复评论、普通 PR 合并或关闭都不适用。
compatibility: 需要已安装并登录的 gh CLI 与 jq
license: MIT
metadata:
  author: DBinK
  version: "0.1.0"
---

# 提交 PR 评审意见（Reviewer 视角）

作为 reviewer，在 `dbk-pr-feedback` 产出评估笔记并与 Agent 定夺完哪些意见需要反馈后，把保留的意见重新编号、按评估笔记的原格式发到目标 PR 的对应代码行（内联评论）。

## 授权前提

本技能**只在用户显式调用时执行**——用户点名 `dbk-pr-submit-review`，或明确要求把定夺好的评估意见发到 PR 内联评论上。调用即视为已授权向目标 GitHub PR 发送评审评论这一对外可见动作。

不要在 `dbk-pr-feedback` 刚写完评估笔记、用户还没确认要发评论时自动进入本流程。

不适用：

- 还在核实、评估意见真伪与价值 → 走 `dbk-pr-feedback`
- 作为 PR 作者修改自己的代码并回复 reviewer → 走 `dbk-pr-execute-reply` 或 `dbk-pr-commit-reply`
- 创建、合并 PR 或排查 CI → 不走本技能

## 工作流

### 1. 锁定评估笔记与目标 PR

1. **读取评估笔记**：
   - 优先使用当前对话中刚刚定夺的 `./notes/review/*.md` 笔记（提及路径时使用绝对路径）；若用户指定了特定笔记文件，则读取该文件。
   - 若用户刚在对话里口头调整了某几条的结论（如“第 2 条不修/不发，第 3 条改成……”）但尚未写回笔记，**先把最终定夺结论同步回评估笔记文件**，保持笔记与即将发出的内容一致。
2. **确认目标 PR**：
   - 从对话上下文、笔记文件名（`<PR编号>-...`）或用户指令中获取目标 `{owner}/{repo}` 与 `{pr_number}`。
   - 若未指定，查询当前分支关联的 PR（`gh pr view --json number,url,headRefOid`）。无法确定目标 PR 时停下来询问用户。

### 2. 筛选条目与重新编号

1. **筛选要发送的条目**：
   - 保留评估结论为需要反馈给 PR 作者的条目（例如修复价值为「必须修」「可选/建议修」，或用户明确指定要发出的条目）。
   - 剔除评估结论为「不属实」「不修 / 不反馈」或用户明确排除的条目。
2. **重新连续编号**：
   - 因剔除了部分条目，对保留下来的条目从 `1` 开始重新连续编号（`## 1. <摘要>`、`## 2. <摘要>`……）。
3. **保持评估笔记原格式**：
   - 每条内联评论的正文（`body`）直接抄录评估笔记中该条目的完整结构（含重新编号后的二级标题，去掉内部定位用的 `- **位置**` 元数据行）：

```markdown
## <新序号>. <意见标题或一句话摘要>

### 是否属实&问题简述

<核实结论 + 问题简述>

### 修复价值

<必须修 / 可选，理由>

### 修复思路（供参考）

<具体修复方案>
```

### 3. 核对 PR Diff 行号坐标

GitHub 内联评论要求 `path` 和 `line` 落在目标 PR 的 diff 范围内：

1. 获取目标 PR 的最新 `head_sha` 与变更文件 diff：
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '.head.sha'
   gh pr diff {pr_number} --repo {owner}/{repo}
   ```
2. 逐条核对笔记中记录的 `<path>` 与 `<line>` 是否存在于该 PR 当前 `head` 的文件及 diff hunk 中（默认 `side: "RIGHT"`，指向新增/修改后的代码行）。
3. 若某条意见指向的行不在 diff hunk 内，或屬於跨文件/整体架构意见无法挂在具体 diff 行上：
   - 优先尝试挂在同文件最相关的变更行上；
   - 若确实没有关联的变更行，将其放入本次 Review 的顶层总评（`body`）中，切勿直接丢弃。

### 4. 提交内联评审（Submit Review）

使用 `gh api` 调用 `POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews` 一次性提交所有内联评论（避免逐条单发造成邮件轰炸）：

```bash
gh api --method POST repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --input - <<'EOF'
{
  "commit_id": "<head_sha>",
  "event": "COMMENT",
  "body": "<可选：无特定代码行归属的整体意见，若全部为内联评论则留空字符串>",
  "comments": [
    {
      "path": "path/to/file",
      "line": 42,
      "side": "RIGHT",
      "body": "## 1. <意见标题或一句话摘要>\n\n### 是否属实&问题简述\n\n...\n\n### 修复价值\n\n...\n\n### 修复思路（供参考）\n\n..."
    }
  ]
}
EOF
```

- `event` 默认使用 `"COMMENT"`（只发评审意见，不擅自 `APPROVE` 或 `REQUEST_CHANGES`，除非用户明确要求拦截或批准）。
- 若某条评论因行号超界导致接口返回 422 Unprocessable Entity，先检查 `gh pr diff` 修正行号后重试。

### 5. 汇报

向用户汇报：

- 所依据的评估笔记**绝对路径**；
- 实际发出的评审条目清单（新序号、原序号对照、挂载的 `path:line`）；
- 被过滤未发送的条目及原因；
- 本次提交的 GitHub Review 链接。

## 注意事项

- 原样抄录格式：每条内联评论直接保留重新编号后的 `## <新序号>. <摘要>` 以及 `### 是否属实&问题简述`、`### 修复价值`、`### 修复思路（供参考）` 三个小节（仅剥离内部定位用的 `- **位置**` 行）。
- 序号务必重新排：比如原笔记有 5 条，排除了第 2、4 条，发出去的 3 条评论标题应当是 `## 1.`、`## 2.`、`## 3.`，不要出现跳号。
- 优先通过一次 `pulls/{pr_number}/reviews` 请求批量提交全部内联评论，不要循环调单条评论接口。
