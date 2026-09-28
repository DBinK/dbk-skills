---
name: dbk-pr-commit-reply
description: 把按 PR 评审意见修好的改动提交、推送到 PR，并逐条回复评审意见；改动跨领域且较多时按领域拆成多次提交。仅在用户显式调用时使用（点名 dbk-pr-commit-reply，或明确要求"把评审修复提交推送并回复评论""评审收尾"）；不要从上下文自动触发。普通 commit/push、只回复评论、只提交不回复、创建或合并 PR、排查 CI 都不适用。
compatibility: 需要 git 与已安装并登录的 gh CLI
license: MIT
metadata:
  author: DBinK
  version: "0.1.0"
---

# PR 评审修复的提交与回复

`dbk-pr-feedback` 的收尾步骤：评审意见已经改好、改动还没提交时，把改动提交、推送到 PR，并逐条回复评审意见。

## 授权前提

本技能**只在用户显式调用时执行**——用户点名 `dbk-pr-commit-reply`，或明确要求把评审修复提交推送并回复评论。调用即视为已授权 commit、push、回复评论这三类对外可见动作。

不要因为对话里出现"修复完成""评审改完了"就自行进入本流程，也不要拿它兜普通开发改动的提交推送。

不适用：还在评估评审意见（走 `dbk-pr-feedback`）、方案已定但代码还没改（走 `dbk-pr-execute-reply`）、只回复评论、只提交不回复、创建或合并 PR、排查 CI。

## 工作流

### 1. 盘点改动

```bash
git status --short
git diff --stat
```

确认哪些改动属于本次评审修复。排除不该进提交的内容：`./notes/review/` 下的评估笔记、调试产物、临时文件、无关的顺手改动。

评审意见还没改完就停下，先跟用户确认，别带着半成品提交。

### 2. 规划提交切分

改动跨多个领域（不同模块、不同评审条目、代码改动 vs 格式化 vs 文档）且量较大时，**按领域拆成多次提交**；单一领域的改动用一个提交。

拆的判据：

- 一个提交只做一件事，message 能一句话说清；
- 尽量让每个提交独立可构建。按领域拆会让某个提交编译不过时，以不破坏构建为先，把相关改动并在一起，或向用户说明取舍；
- 同一文件里混着无关改动、且拆开不影响构建时，用 `git add -p` 分离；
- 不要为拆而拆：同一议题的相邻小改动放一个提交。

三个以上提交、或涉及关键模块时，先把提交清单（几个提交、各含哪些文件、message 是什么）给用户过一遍再动手。

### 3. 提交

提交前按语言栈跑门禁（Rust 项目走 `dbk-rust-gates`，没有对应技能时按项目约定）。提交 message 风格对齐仓库既有习惯（`git log --oneline -20`），说清"按哪条评审意见改了什么"。

```bash
git add <paths> && git commit -m "..."
```

### 4. 推送

```bash
git push
```

只有当分支已与远端分叉、确实需要时才强推，且必须用 `--force-with-lease` 并先问用户。默认不强推。

### 5. 逐条回复评审意见

先列出评审评论和它们的 id：

```bash
# in_reply_to_id 为 null 的是顶层评审评论
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '.[] | {id, path, line, in_reply_to_id, body}'
```

对每条意见回复到它所在的**内联 discussion**：

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="..."
```

回复里说清结论：已修（简述怎么改的、在哪个提交）/ 不修（说明理由）。一条意见一条回复，别把多条意见揉成一条 PR 级总评论；不得不在 PR 级评论里回复时，正文 @ 该 reviewer。

### 6. 汇报

向用户列：提交清单（hash + message）、push 结果、逐条回复了哪些意见、有没有没回的意见及原因。push 后 CI 会重跑，把链接一并给出。

## Gotchas

- 回复必须挂在对应的内联 discussion 上；只发一条总评论时，reviewer 在原讨论里看不到回复，会以为你漏了。
- `./notes/review/` 笔记默认是本地评估材料，不进提交；项目若有版本化评审记录的约定，先问用户。
- 回复不会自动 resolve discussion，要不要标记已解决由用户决定，别擅自点。
- 强推会重置 PR 时间线，可能让既有评论的行号错位；能不强推就不强推。
- 门禁在提交前跑，别等 push 后 CI 红了再补。
- 交付时如果改动跨了多个评审条目，回复和提交要对得上：哪条意见对应哪个提交，别张冠李戴。
