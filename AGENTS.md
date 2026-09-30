# dbk-skills 仓库开发指南

本仓库是个人 Agent Skills 集合，通过 [skills CLI](https://github.com/vercel/skills)（`npx skills add DBinK/dbk-skills -g`）分发。本文件指导 Agent 在本仓库内开发。

## 开发前必读

**动手开发前，先加载 `skills/base/dbk-agent-rules/SKILL.md`，按其协作准则执行。**

**开发、修改、迭代任何 skill 之前，先加载 `skills/base/dbk-skill-dev/SKILL.md` 并按其工作流执行。**

`dbk-skill-dev` 的核心要求（详见该文件）：

- 格式规范以 https://agentskills.io/llms.txt 为唯一事实标准，动手前先拉取索引和对应页面，不要凭记忆写。
- description 是唯一的触发机制，必须同时说明"做什么"和"何时用"，并列出用户真实会说的话。
- 改完技能后要跑校验和触发测试，不要只改文字不验证。

## 目录结构

```
skills/
├── base/            # 协作硬规则与元技能
├── languages/       # 语言栈约定
└── git-workflow/    # git / PR 工作流
```

约定：

- skill 目录名 = frontmatter `name`，统一带 `dbk-` 前缀
- 分类文件夹只用于组织，新增 skill 放进对应分类即可
- 触发评估查询集（可选产物）放在各 skill 的 `evals/trigger-queries.json`

## 测试与验证

1. **格式校验**：用官方校验工具 [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) 检查 frontmatter 合法性（name 小写连字符、description ≤1024 字符等）。

   优先用 `uvx` 直接跑：免安装，每次按最新版解析（想强制刷新加 `--refresh`）：

   ```bash
   uvx skills-ref validate ./skills/<分类>/<skill名>
   ```

   不想走 PyPI 时，可从公开源码仓库直接跑，不必克隆：

   ```bash
   uvx --from 'git+https://github.com/agentskills/agentskills#subdirectory=skills-ref' skills-ref validate ./skills/<分类>/<skill名>
   ```

   两条已核实的坑：PyPI 元数据里的 Repository 链接（`github.com/anthropics/agentskills`）已 404，公开仓库是 `agentskills/agentskills`；两个来源的版本会错开——实测 PyPI 是 **0.1.1**，而仓库 main 的 `pyproject.toml` 仍写 0.1.0，所以别假设"源码形式更新"，以 `skills-ref --version` 实际输出为准。

   注意：`uvx skills-ref` 不带子命令时会打印用法并以退出码 2 结束，这是正常行为，不是安装失败。

   需要固定版本或离线使用时，退回本地安装：

   ```bash
   git clone https://github.com/agentskills/agentskills /tmp/opencode/agentskills
   uv tool install /tmp/opencode/agentskills/skills-ref
   skills-ref validate ./skills/<分类>/<skill名>
   ```

   没有条件安装时，对照 specification 手工复核 frontmatter 约束。
2. **本地接入**：两种方式任选：

   ```bash
   # 方式一：用 skills CLI 从本地路径安装
   npx skills add ./skills -g        # 或指定单个 skill 目录
   ```

   或

   ```bash
   # 方式二：符号链接到发现路径，改动能即时生效
   ln -s ../../skills/<分类>/<skill名> .agents/skills/<skill名>
   ```

   新会话中确认 skill 能被发现。

3. **触发实测**：用 `evals/trigger-queries.json` 里的正负例查询做无头运行，检查目标 skill 是否被加载。查询集是可选产物，默认跟随仓库现状：有就按下面跑实测，没有就提醒用户"可以建一套查询集来实测触发率"，不要主动补建，也不要跳过验证直接宣称改好了。

   仓库里带了示例脚本 `skills/base/dbk-skill-dev/scripts/run_trigger_eval.py`，以 pi 为例：

   ```bash
   uv run skills/base/dbk-skill-dev/scripts/run_trigger_eval.py \
     skills/<分类>/<skill名>/evals/trigger-queries.json <skill名> --runs 1
   ```

   脚本要求 Python 3.10+：`uv run` 会按脚本内的 PEP 723 元数据自动挑解释器，也可以直接用任意 3.10+ 的 `python3` 执行。

   判定标志是"agent 是否真的读了技能正文"。换客户端时把脚本里的启动命令和判定方式一起替换，各客户端的判定位置：

   - omp：输出里出现 `skill://<skill名>`
   - claude：名为 `Skill` 的 tool_use
   - opencode：加载日志出现 `Loaded skill: <name>`，若 `opencode run` 不回显，改用会话导出后 grep

   注意别用"输出里出现 SKILL.md 路径"这种朴素判定——多数客户端会把技能清单连同路径一起注入系统提示，那样每条查询都会判成触发。

   正例应触发、负例不应触发；不过关就迭代 description 再测。`--runs 1` 只用于粗筛，判定回归要对新旧两版同口径各跑多次，不能只看单次结果。

## 注意

- 本仓库全是文本文件，没有 LSP 兜底。**修改任何文件后，必须手动检查所有相关引用是否同步更新**：skill 改名/移动时，README 分类表、安装命令、`.agents/skills/` 符号链接、AGENTS.md 中的路径都要跟着改。
- 所有改动只修改文件，add/commit/push 由用户决定。
