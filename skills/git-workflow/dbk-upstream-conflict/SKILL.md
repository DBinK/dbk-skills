---
name: dbk-upstream-conflict
description: 把上游主分支的变更合并进当前分支，并处理由此产生的 git 冲突。用户显式调用本技能却没给其他指令时，默认动作就是从上游拉取主分支合并到当前目录；当用户说"从上游拉取主分支合并""把 origin main 合到当前分支""同步上游"时同样使用。merge/rebase/cherry-pick 出现冲突、同步 origin main 或 upstream 更新导致冲突、用户说"解决冲突""更新完 main 有冲突"时也使用。不适用于普通分支切换、与上游主分支无关的本地分支间合并或冲突（如两个本地分支的 package-lock.json 打起来了），或只想弄清冲突原因而不执行合并。
license: MIT
compatibility: 需要 git；Cargo.lock 重建需 cargo 工具链
metadata:
  author: DBinK
  version: "0.3.0"
---

# 上游合并冲突处理

两个入口：

- **主动调用**：用户显式调用本技能、且没写其他指令——默认任务就是把上游主分支合并进当前分支。
- **被动触发**：用户在做合并（merge/rebase/cherry-pick）或同步上游时撞上冲突，让 Agent 处理。

## 主动调用（默认流程）

用户只丢来一个技能名、没写别的，就按下面的默认动作走：把上游主分支的最新变更合并进当前分支。

1. **看工作区状态**：`git status`。有未提交改动先停下问用户，别把无关改动混进这次合并。
2. **确认上游 remote 和主分支名**：默认 remote `origin`、分支 `main`；项目用 `upstream` remote 或 `master` 时按实际取。拿不准就用 `git remote -v` 看有哪些 remote，别照默认硬套。
3. **拉最新**：`git fetch <remote> <main> --no-tags`。
4. **合并**：`git merge <remote>/<main>`（遵循 merge 优先，不用 rebase）。
5. **看结果**：无冲突则合并自动完成；有冲突转下文的冲突处理规则。

主动调用本身即视为对本轮 fetch + merge 的授权。push 不在范围内，需要用户另外明说。

## 处理原则

1. **先理解双方意图再动手**：逐个冲突文件搞清楚——本分支新增了什么，上游改了什么，为什么撞上。
2. **目标是保留本 PR 新增功能的同时吸收上游变化**，而不是简单二选一或"以上游为准"了事。
3. **设计层面的冲突停下来**：如果两边的改法在方案上互斥（比如接口设计不同、同一逻辑两种实现思路），无法机械合并——列出冲突点、双方方案和可选路径，让用户决策后再继续。不要替用户拍板。

## Cargo.lock 冲突（gotcha）

Cargo.lock 的冲突**不用手工解决**。先把 Cargo.toml 合并正确，然后重建 lock 文件：

```bash
git fetch <remote> <main> --no-tags && git restore --source <remote>/<main> -- Cargo.lock && cargo check
```

`cargo check` 会按合并后的 Cargo.toml 重新生成一致的 Cargo.lock。仅 Rust 项目适用。

## CHANGELOG 冲突（Keep a Changelog）

`CHANGELOG.md` 用 Keep a Changelog 格式时，解完冲突**把本分支新增的条目排在 `## [Unreleased]` 段落末尾**（子段落 `### Added` / `### Fixed` 等同理），上游条目放前面：

```markdown
## [Unreleased]

### Added

- 上游新进的条目

- 本分支新增的条目 ← 固定排在末尾
```

上游后续新增条目一般仍落在 Unreleased 顶部，本分支内容固定在末尾，两边改动位置错开，下次合并就不容易再撞冲突。两边的条目都要保留，不要整段选某一侧。

## 边界

- "解决冲突"= 把工作区文件改到正确的合并结果 + `git add` 标记已解决。
- **冲突合并的收尾 commit 仍需用户明确同意**：解完冲突、`git add` 之后先停下，等用户点头再 commit。主动调用下的干净合并由 `git merge` 自行完成，不用额外确认。
- push 一律不在本技能范围内，需要用户另外明说。
- 冲突量大或涉及关键模块时，先给用户一份冲突清单和逐项处理计划，确认后再批量动手。

## Gotchas

- 解冲突前确认基线：fetch 最新的上游引用，别基于过期的 origin main 判断。
- `git checkout --theirs/--ours` 在 merge 和 rebase 中方向相反（merge 中 ours=当前分支，rebase 中 ours=被 rebase 到的基线），用之前想清楚方向，拿不准就手工编辑。
- 解决完一个文件的冲突要跑编译/测试验证语义正确，文本层面无冲突标记 ≠ 逻辑合并成功。
