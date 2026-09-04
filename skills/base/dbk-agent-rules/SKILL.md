---
name: dbk-agent-rules
description: 用户与 Agent 协作的指导规则，适用于任何代码开发任务。只要用户在讨论、阅读、编写或修改代码——包括实现功能、修 bug、重构、代码评审、命名讨论、git 操作（add/commit/push）、技术方案评估、答疑咨询等——都必须先加载本技能再行动，即使用户没有提到"习惯""规范""约定"等字样，也不管任务多小。包含回答语言、咨询类与改动类指令的边界、git 操作限制、命名建议方式、工具选型偏好（gh/context7/paper-search/rg/fd/bat/sd）、文件删除安全等必须遵守的规则。
license: MIT
metadata:
  author: DBinK
  version: "0.1.1"
---

# Agent 协作准则

以下是用户与 Agent 协作的准则，适用于任何任务，无论大小。与 AGENTS.md 内容一致；两者都在时同样执行。

## 规则

1. **始终用中文回答**。
2. **用户不会说反问句**。所有疑问句都是正常询问，客观回答即可，不要解读成质问或反讽。
3. **区分指令类型再动手**：
   - **咨询类**（"看看""评估下""怎么样""有什么方案"）→ 只分析/评估，**不要改动任何文件**。这类决策需要人工检查方案、确定方向。
   - **改动类**（"改掉""加上""修复""重构成"）→ 只修改文件。
4. **git 操作熔断**：改动类任务中**禁止执行 add / commit / push 等任何会产生历史记录或对外可见的动作**，除非用户在该次对话里明确要求。这些动作需要人工复核。
5. **merge 优先**：默认用 `git merge` 集成分支、同步上游，不用 rebase。例外：用户明确要求 rebase、目标仓库要求线性历史（如强制 squash merge）、整理自己的私人分支历史。
6. **命名问题只推荐不改**：用户问命名时，列出若干候选名并各自给出理由，**不要直接改代码里的名字**，由用户拍板。

## 判断示例

| 用户说                                | 类型     | 动作                                 |
| ------------------------------------- | -------- | ------------------------------------ |
| "这个函数这样写有没有性能问题？"      | 咨询     | 只分析，不改                         |
| "把这个循环优化一下"                  | 改动     | 改文件，不 commit                    |
| "`target_dir` 这个名字是不是不太好？" | 命名咨询 | 给候选名+理由，不改                  |
| "改成 `target_path` 吧"               | 改动     | 改文件，不 commit                    |
| "提交一下吧"                          | 明确要求 | 允许 commit（仍不要 push，除非明说） |

## 工具使用

- **GitHub 交互**：Agent 自带的 PR / issue 相关工具优先；覆盖不到的场景用 `gh` CLI（环境中已安装并登录）。
- **学术搜索**：统一使用 paper-search-mcp。未安装时先装：`uv tool install paper-search-mcp`，用法参考 https://github.com/openags/paper-search-mcp/blob/main/claude-code/SKILL.md
- **库/框架文档查询**：统一使用 context7 CLI + skills，**优先于其他 web 搜索**。
- **现代化命令行工具**：环境里已有下列替代品，写命令时直接优先使用，不要退回传统命令：

  | 传统 | 用这个         |
  | ---- | -------------- |
  | grep | `rg` (ripgrep) |
  | find | `fd`           |
  | cat  | `bat`          |
  | sed  | `sd`           |

- **缺失工具的安装顺序**：linuxbrew > cargo binstall > apt > 官方安装脚本 > cargo install；都不可行就放弃安装并改用传统命令。

## 数据安全

- **删除文件一律进回收站，禁止 `rm`**。依次尝试环境中已装的回收站工具：`gio trash` > [gomi](https://github.com/babarot/gomi) > [trash-cli](https://github.com/andreafrancia/trash-cli)；都没有时停下来询问用户，不要直接 rm。

## 相关技能路由

本技能加载后，若任务命中下列场景，继续加载对应技能再行动：

| 场景                          | 技能                    |
| ----------------------------- | ----------------------- |
| Rust 项目里要 commit/push     | `dbk-rust-gates`        |
| 写/改 Python 代码             | `dbk-python-style`      |
| 创建 worktree、开分支并行开发 | `dbk-git-worktree`      |
| 合并上游出现冲突              | `dbk-upstream-conflict` |
| 处理 GitHub PR 的评审意见     | `dbk-pr-feedback`       |

## Gotchas

- "顺便提一下""记得提交"这类顺带指令也算明确要求，但拿不准就先问一句再执行。
- 咨询类任务即使发现明显 bug 也只指出，不顺手修。
