---
name: dbk-git-worktree
description: 创建 git worktree 并行开发环境。当用户要开 worktree、为某个任务新开独立目录/分支干活、要并行处理两件事互不干扰时使用——即使用户没说出"worktree"这个词（比如"另开个环境改这个""开个分支处理一下"）。流程：先提议分支名并等用户确认，再创建到 ../<项目名>.worktrees/<分支名最后一层> 下；重名时加后缀区分。不适用于普通切分支（git checkout/swtich）或在当前目录继续开发。
---

# worktree 创建

为并行任务创建 git worktree。纪律：**先给分支名建议，用户确认后才创建**。

## 流程

### 1. 提议分支名

先看仓库现有分支了解命名风格：

```bash
git branch -a --format='%(refname:short)' | head -30
```

提议一个完整分支名，两段式或三段式均可，参考仓库现有分支风格选择：

- 三段式 `<类型>/<范围>/<名称>`：名称需要附加上下文时用（关联的任务、模块或问题），如 `feat/f-1354/add-login`、`fix/null-check/buffer-overrun`
- 两段式 `<类型>/<名称>`：无额外上下文时用，更简洁，如 `feat/add-login`、`fix/null-guard`

**最后一层命名规则**：一般控制在 2 个词以内，特殊情况最多不超过 3 个词，单词间用连字符。例：`fix/f-1354/fix-toml` 中最后一层是 `fix-toml`；两段式 `fix/fix-toml` 中最后一层是 `fix-toml`。

### 2. 等用户确认

把建议的分支名给用户确认。未确认前不要执行任何创建动作。

### 3. 创建 worktree

确认后，创建到项目同级目录下：

```bash
git worktree add ../<项目名>.worktrees/<分支名最后一层> -b <完整分支名>
```

示例：

```bash
# 三段式
git worktree add ../my-app.worktrees/fix-toml -b fix/f-1354/fix-toml
# 两段式
git worktree add ../my-app.worktrees/add-login -b feat/add-login
```

- `<项目名>` 取当前仓库根目录名（`git rev-parse --show-toplevel` 的 basename）
- 目录用 `.worktrees`（复数）

### 4. 重名处理

目标目录已存在时，添加后缀等方式区分（如 `-2`），并把最终用的名字告诉用户。

### 5. 收尾

创建成功后告知用户 worktree 路径及进入方式（`cd <路径>`）。

## Gotchas

- worktree 与主仓库共享同一个 `.git`，在 worktree 内正常 add/commit 即可，但 commit/push 仍遵守"用户明确要求才做"的规则。
- 同一分支不能同时被两个 worktree 检出；如果分支已存在且被占用，提示用户换名或复用现有 worktree。
- 新建的 worktree 里需要重新构建（target/node_modules 等不共享），首次使用前提醒用户。
