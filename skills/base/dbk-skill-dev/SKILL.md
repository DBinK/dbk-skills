---
name: dbk-skill-dev
description: Agent Skill 的全生命周期开发：从零创建新技能、把现有工作流沉淀为技能、修改或扩充已有技能、迭代改进技能行为与输出质量、修复不触发或误触发的技能、优化 description 触发准确率、评估与打包。当用户想创建、改动、迭代任何 skill，或反馈某个 skill 触发不准/效果不好时使用。本技能以 https://agentskills.io/llms.txt 为唯一事实标准，实时拉取最新文档，不依赖本文件里写死的规则。
license: MIT
compatibility: 需要网络访问 agentskills.io；校验可选 skills-ref CLI
metadata:
  author: DBinK
  version: "0.1.0"
---

# Skill Dev

Agent Skill 的全生命周期开发：创建、修改、迭代、评估、打包。Agent Skills 的格式规范**没有**写死在本文件里——而是实时从 agentskills.io 官方文档拉取，保证格式演进时规则始终是最新的。

本文件是**工作流**。拉取的文档才是**唯一权威**的格式细节来源（frontmatter 字段、约束、目录约定、渐进式披露、eval schema、校验工具等）。

## 核心原则：llms.txt 是唯一事实标准

**https://agentskills.io/llms.txt 是本技能的唯一事实标准。** 它提供全部官方文档的活索引，所有格式规则都以它及其指向的页面为准。不要凭记忆或本文件里的示例写技能——永远先拉取 llms.txt 获取索引，再按需拉取对应页面。如果本文件内容与拉取的文档冲突，一律以拉取到的文档为准。

## 工作流

### 1. 加载文档索引

拉取 Agent Skills 全部文档的活索引：

- `https://agentskills.io/llms.txt`

它列出了所有可用页面。用它来确认**当前**的页面列表——不要假设下一步列出的页面名仍然正确。

### 2. 拉取需要的页面

根据任务拉取对应页面（具体 URL 以第 1 步的索引为准）：

| 任务 | 拉取 |
| --- | --- |
| 任何创建 / 编辑 / 格式问题 | `specification.md` —— 格式规范：SKILL.md frontmatter、name/description 约束、目录结构、可选目录、渐进式披露、文件引用 |
| 第一次做 / 最小示例 | `skill-creation/quickstart.md` —— 一个最小的可用技能 |
| 设计技能内容 | `skill-creation/best-practices.md` —— 范围界定、控制力度、指令模式、gotchas、模板 |
| 验证技能是否好用 | `skill-creation/evaluating-skills.md` —— 测试用例、evals/evals.json schema、baseline 运行、评分、迭代循环 |
| 优化触发准确率 | `skill-creation/optimizing-descriptions.md` —— 触发评估查询、调优 `description` |
| 打包可执行代码 | `skill-creation/using-scripts.md` —— 如何设计和打包脚本 |
| 给 agent/客户端加支持 | `client-implementation/adding-skills-support.md` —— 仅当任务是关于客户端而非技能时 |

任何涉及 SKILL.md 格式本身的任务都要拉 `specification.md`。新建技能时至少要拉 `specification.md` 和 `best-practices.md`；任务需要时再拉其他页面。

### 3. 创建、编辑或迭代技能

按拉取到的实时规范执行。以下是需要向拉取文档核实的要点（这些只是指引，不是权威规则——每一条都要复核）：

- `SKILL.md` 包含 YAML frontmatter（`name` + `description` 必填）+ Markdown 正文。
- `name` 符合文档规定的约束，包括必须与父目录名一致。
- `description` 同时说明技能**做什么**和**何时用**——这是主要的触发机制。
- 目录布局遵循文档约定（`scripts/`、`references/`、`assets/`）。
- 指令采用渐进式披露：主 `SKILL.md` 保持精简，把细节放进按需读取的 reference 文件。

编辑已有技能时：保留原 `name`，不改父目录名；除非路径只读，否则在原位置修改。

### 4. 校验

查看刚拉取的 `specification.md` 中当前的校验工具（例如 `skills-ref validate ./my-skill`），可用则运行。它会检查 frontmatter 是否合法、是否符合命名约定。如果没有校验工具，就对照规范手工复核 frontmatter 约束。

### 5. 测试与迭代

**迭代是常态而非收尾**：技能第一次写完往往不是最终形态，要在真实使用中持续打磨。

- 用户反馈技能"没触发""误触发""效果不好"时，先定位问题类型：
  - 该触发没触发 / 不该触发却触发 → 按 `optimizing-descriptions.md` 调 `description`（触发评估查询 + train/validation 循环）
  - 触发了但输出质量差 → 按 `evaluating-skills.md` 的 eval 工作流：写 2-3 个真实测试提示词，带技能和不带技能（baseline）对比运行，评分并迭代
- 每次用户纠正了技能的行为，把纠错沉淀回 SKILL.md 的 Gotchas 或对应步骤，避免重复犯错。

### 6. 打包与呈现

如果用户想要可安装的产物，查看规范中当前的打包约定（例如 `.skill` 文件），按约定产出。

## 范围护栏

- 如果用户问的是**使用**技能（调用、加载），而不是**创建/修改/迭代**技能，本技能不适用。
- 如果用户问的是某个具体产品的技能系统（如 VS Code、Claude Code、Copilot），拉取的规范页面可能涵盖发现路径——但产物格式仍需符合标准 Agent Skills 规范。
