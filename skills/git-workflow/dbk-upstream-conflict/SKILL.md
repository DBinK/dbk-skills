---
name: dbk-upstream-conflict
description: 处理合并上游变更时产生的 git 冲突。当 merge/rebase/cherry-pick 出现冲突、同步 origin main 或 upstream 更新导致冲突、用户说"解决冲突""合并上游""更新完 main 有冲突"时使用。核心原则：先评估如何保留本分支/PR 新增功能再吸收上游变化，设计层面的冲突停下来让用户决策；Cargo.lock 冲突有标准重建流程，不手工解。
license: MIT
compatibility: 需要 git；Cargo.lock 重建需 cargo 工具链
metadata:
  author: DBinK
  version: "0.1.0"
---

# 上游合并冲突处理

典型场景：把上游变更（origin main）合并进当前 PR 分支时出现冲突。

## 处理原则

1. **先理解双方意图再动手**：逐个冲突文件搞清楚——本分支新增了什么，上游改了什么，为什么撞上。
2. **目标是保留本 PR 新增功能的同时吸收上游变化**，而不是简单二选一或"以上游为准"了事。
3. **设计层面的冲突停下来**：如果两边的改法在方案上互斥（比如接口设计不同、同一逻辑两种实现思路），无法机械合并——列出冲突点、双方方案和可选路径，让用户决策后再继续。不要替用户拍板。

## Cargo.lock 冲突（gotcha）

Cargo.lock 的冲突**不用手工解决**。先把 Cargo.toml 合并正确，然后重建 lock 文件：

```bash
git fetch origin main --no-tags && git restore --source origin/main -- Cargo.lock && cargo check
```

`cargo check` 会按合并后的 Cargo.toml 重新生成一致的 Cargo.lock。仅 Rust 项目适用。

## 边界

- "解决冲突"= 把工作区文件改到正确的合并结果 + `git add` 标记已解决。
- 完成合并的 commit / push / 继续后续动作仍需用户明确同意后才执行。
- 冲突量大或涉及关键模块时，先给用户一份冲突清单和逐项处理计划，确认后再批量动手。

## Gotchas

- 解冲突前确认基线：fetch 最新的上游引用，别基于过期的 origin main 判断。
- `git checkout --theirs/--ours` 在 merge 和 rebase 中方向相反（merge 中 ours=当前分支，rebase 中 ours=被 rebase 到的基线），用之前想清楚方向，拿不准就手工编辑。
- 解决完一个文件的冲突要跑编译/测试验证语义正确，文本层面无冲突标记 ≠ 逻辑合并成功。
