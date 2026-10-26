# Worktrunk 配置与使用指南 (dbk-git-worktree 增强)

本指南介绍如何将 Worktrunk (`wt`) 集成到 `dbk-git-worktree` 工作流中，以获得并行开发环境的自动化增强。

## 1. 初始化安装

若系统未安装 `wt`，请参考 [Worktrunk 官网](https://worktrunk.dev) 安装。安装完成后，运行：

```bash
wt config create
```

## 2. 核心配置模版 (用户级)

将以下配置复制到 `~/.config/worktrunk/config.toml`。此配置与 `dbk-git-worktree` 规则完全兼容，并开启了构建缓存共享：

```toml
# ../<repo>.worktrees/<分支名最后一段>
# 自动对齐 dbk-git-worktree 命名规范，确保并行开发工作区目录结构的一致性
worktree-path = "{{ repo_path }}/../{{ repo }}.worktrees/{{ branch | basename | sanitize }}"

[switch]
# 创建/切换工作区后自动切换当前 shell 工作目录 (配合 shell integration)
cd = true

[commit]
# 仅 stage 已跟踪文件，不自动包含未跟踪文件，防止开发环境中的临时文件污染提交记录
stage = "tracked"

[merge]
# 使用 merge 集成：禁止 squash/rebase，始终生成 merge commit，保留完整历史记录
squash = false
rebase = false
ff = false
commit = false
remove = false

[remove]
# 删除工作区时自动清理关联分支 (仅已合并分支)，减少过期分支堆积
delete-branch = true

[post-start]
# 核心能力：利用文件系统 CoW (copy-on-write) 机制
# 在创建工作区时瞬间克隆已有的依赖目录 (node_modules) 和构建产物 (Rust target/)
# 彻底消除了切换分支后需重新编译或重新 install 的冷启动等待
copy-cache = "wt step copy-ignored"
```
## 3. 在 Agent 执行中的调用逻辑

在执行 `dbk-git-worktree` 任务时，应遵循以下流程：

1. **检测环境**：
   ```bash
   command -v wt >/dev/null 2>&1 && echo "Worktrunk installed"
   ```
2. **决策路径**：
   - **已安装 `wt`**：优先使用 `wt switch --create <branch>`。它将自动触发 `post-start` 钩子，通过 `wt step copy-ignored` 实现瞬间构建。
   - **未安装 `wt`**：提示用户："检测到未安装 Worktrunk，推荐安装以开启并行开发缓存共享，是否需要安装指南？"，随后继续执行原生的 `git worktree add` 流程。
3. **确认与执行**：
   - 保持分支命名规范的询问纪律。
   - 成功后，若使用 `wt`，无需额外提醒重建；若使用 `git worktree`，提醒用户手动构建。
