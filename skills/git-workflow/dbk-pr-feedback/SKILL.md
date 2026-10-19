---
name: dbk-pr-feedback
description: 评估外部或上下文中的代码评审反馈(review comments / review 意见)：逐条核实每条意见是否属实、值不值得修、修复思路是什么，写入 notes/review/ 评估笔记并给出绝对路径，与用户定夺处理方式。支持任意来源的评审意见：默认检查当前分支对应 PR 上未处理的意见；也支持用户指定其他 PR（编号或链接），或直接评估对话上下文中粘贴、转发、其他 Agent 产出的 review 意见（即使未提及 PR）。当用户让你看、评估、处理评审意见（如"看下 PR 的意见""还有哪些 review 没处理""评估一下这几条 review 意见写到评估笔记里"），让你判断某条意见说得对不对、属实吗，提到 reviewer、CodeRabbit 或其他 Agent 留下的评审意见，或给出 PR 链接时使用。只做到产出并定夺评估笔记为止，改代码、提交推送、回复评论或作为 reviewer 发内联评论走后续技能；对本地未提交改动从零做一般 code review、自查代码质量、创建或合并 PR、排查 CI 失败等任务不适用，勿触发本技能。
compatibility: 需要已安装并登录 gh CLI（拉取 GitHub PR 意见时）
license: MIT
metadata:
  author: DBinK
  version: "0.3.0"
---

# 评审意见评估

评估来自 GitHub PR 或对话上下文的评审意见（兼顾 **PR 作者自查外部反馈** 与 **作为 Reviewer 审查他人 PR** 两种场景）。核心纪律：**先核实，再定夺**——不马上照单全收别人的意见，也不在定夺前直接动手改代码或对外发评论。

## 工作流

### 1. 定位与获取评审意见

按以下优先级确定意见来源，并聚焦**未处理/未解决**的意见：

1. **对话与上下文指定（最高优先级）**
   - 用户在对话中直接粘贴、转发了评审意见，或要求评估 Agent 上下文里已有的意见（例如其他工具/Agent 产出的 review 结论）→ 直接以该内容为准，无需拉取 PR。
2. **用户指定 PR**
   - 用户给出了具体的 PR 编号或链接（可能属于当前仓库的其他分支，或跨仓库 PR）→ 拉取该指定 PR 上未处理的评审意见。
3. **默认：当前分支关联的 PR**
   - 用户未指定具体意见或 PR 时，默认查询当前分支对应的 PR：
     ```bash
     gh pr view --json number,url,headRefName,headRefOid,baseRefName
     ```
   - 若当前分支没有关联 PR，且上下文中也无待评估意见，向用户询问要处理的 PR 编号/链接或具体意见内容。

**拉取 PR 未处理意见的方法**：

系统已安装 `gh` CLI 且已登录。拉取 PR 评论时，优先用 GraphQL 过滤掉已解决（`isResolved: true`）和已过时的内联线程，同时结合 PR 级评论综合判断：

```bash
# 1. 拉取 review threads（可精确过滤 isResolved == false 的未处理内联意见）
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            isResolved
            isOutdated
            path
            line
            comments(first: 20) {
              nodes {
                databaseId
                author { login }
                body
                createdAt
              }
            }
          }
        }
      }
    }
  }' -F owner='{owner}' -F repo='{repo}' -F pr={pr_number}

# 2. 拉取 PR 级 reviews 与普通 issue 评论（检查是否有顶层未处理的评审意见）
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews
gh api repos/{owner}/{repo}/issues/{pr_number}/comments
```

### 2. 定位并同步目标代码（确保看到最新工作）

核实意见前必须确保读取的是**目标 PR（或目标分支）的最新代码**，切勿直接拿本地未同步的旧代码或无关分支去核对。按以下顺序定位与同步：

1. **当前工作区正好是目标 PR 分支**：
   - 先 `git fetch` 检查本地 `HEAD` 是否落后于远端最新提交（`headRefOid`）。
   - 若落后于远端，先检查 `git status --porcelain`：工作区干净时执行 `git pull --ff-only`（或 `git merge`）拉取最新代码；若有未提交改动无法直接拉取，先告知用户或直接读取 `origin/<headRefName>` 的内容，绝不擅自 reset/stash 抹掉本地改动。
2. **当前工作区不是目标分支 → 查找已有 Worktree**：
   - 运行 `git worktree list` 检查本地是否已有检出该分支的工作树（含 `.worktrees/` 下的目录）。
   - 若找到对应 worktree，在该 worktree 中确认工作区干净后拉取最新代码（`git -C <worktree_path> pull --ff-only`），直接读取该目录下的文件进行核实。
3. **本地同仓库但无对应 Worktree**：
   - 先 `git fetch origin pull/<pr_number>/head` 将 PR 最新提交拉到本地对象库。
   - 轻量核实可结合 `gh pr diff <pr_number>` 与 `git show FETCH_HEAD:<path>`查看；需要跨多文件检索时，可在临时目录建立只读工作树（如 `git worktree add --detach /tmp/pr-review-<pr_number> FETCH_HEAD`）或浅克隆。
4. **跨仓库 PR（本地无该仓库）**：
   - 轻量核实用 `gh pr diff` 与 `gh api repos/{owner}/{repo}/contents/<path>?ref=<head_sha>` 在线读取；复杂项目可用 `git clone --depth=1` 浅克隆目标分支到 `/tmp/pr-review-<repo>-<pr_number>` 后核实。

### 3. 逐条评估

基于最新代码，按意见顺序对每条待处理意见依次回答三个问题：

1. **是否属实** —— 先核实代码事实。评审意见可能是误读、基于旧版本代码、或与项目约定冲突，发现不属实要如实说明，不盲从。
2. **修复价值** —— 属实的话值不值得修？区分：必须修 / 可修可不修 / 不建议修（说明理由）。
3. **修复思路** —— 怎么修？给具体方案而不是空话。

设计层面的分歧（比如架构取舍、两种方案各有道理）：不要替用户拍板，列出选项和利弊让用户决策。

### 4. 写入评估笔记与定夺

把评估写入**当前主对话工作区**根目录 `./notes/review/` 下（目录不存在则创建，即使去别的 worktree 或临时目录读了代码，笔记也统一写在当前工作区下）：

- **文件名格式**：
  - 来自 PR：`<PR编号>-<YYMMDD>-<HHMM>-<简短主题>.md`，例如 `158-260805-1358-something.md`
  - 来自上下文/非特定 PR：`context-<YYMMDD>-<HHMM>-<简短主题>.md`，例如 `context-260805-1358-something.md`
  - 时间取写笔记时的本地时间，主题用简短小写英文、短横线连接
- 目录里已有的旧笔记不回溯改名
- 格式参考同目录已有文件；无参照时用下面的模板
- **行文口吻（角色中立）**：各小节正文统一采用**客观陈述句**直接描述代码事实、触发条件、影响与修改方案（例如：“属实。当 X 为空时第 42 行解引用会触发 panic……”），不写“reviewer 说得对”“建议你改一下”等人称指代。这样笔记既可作为作者自查依据，也可在作为 Reviewer 时直接原样抄去发内联评论。
- 按意见顺序排列，一条意见一个二级标题；每条意见记录关联的文件路径与行号（便于后续定位改代码或发内联评论）

```markdown
# <PR #<编号> | 上下文> 评审意见评估

## <序号>. <意见标题或一句话摘要>

- **位置**：`<path/to/file>:<line>`（若针对整体设计无特定行号，写关联文件或模块）

### 是否属实&问题简述

<核实结论 + 问题简述>

### 修复价值

<必须修 / 可选 / 不修，理由>

### 修复思路（供参考）

<具体修复方案>
```

- **路径引用要求**：写完笔记向用户汇报评估结论，以及后续任何时候提到该评估文档路径时，**必须使用绝对路径**（例如 `/Users/xxx/project/notes/review/158-260805-1358-something.md`），不要只写相对路径。
- 若用户对某些条目的结论或修复方案提出了修改意见，将定夺后的结果同步更新回评估笔记中。

### 5. 收尾与下一步分流

本技能**只做到产出并定夺评估笔记为止**，不修改项目业务代码，也不执行 git commit / push 或对外发送 PR 评论。

汇报完评估结论与笔记的绝对路径（或按用户意见更新完笔记）后，主动提示用户选择下一步：

- **作为 PR 作者（要改代码并回复评审）**：询问是否调用 `dbk-pr-execute-reply`，按定夺好的方案改代码、分段提交、推送到 PR 并逐条回复评审意见。
- **作为 Reviewer（要把意见发给提 PR 的人）**：询问是否调用 `dbk-pr-submit-review`，把定夺后需要反馈的意见（重新编号并保留 `## <序号>. <摘要>` 及下方小节的原格式）发到对应 PR 的内联评论上。

两个后续技能均须等用户明确确认或显式调用后再执行。

## 注意事项

- 评估前务必按第 2 步确认读到的是目标分支的最新代码：评审意见可能在新提交里已经被修掉，或者你在看别人的 PR 而本地分支还停留在旧版本。
- CodeRabbit 等机器人或上下文中其他 Agent 的意见同样先过评估流程，不要盲从。
- 一批意见里通常混着「真问题」和「风格偏好」，评估时分开标注，别混为一谈。
- 提及评估笔记路径时始终输出绝对路径，确保用户在终端或 IDE 中可直接点击跳转。
