---
name: dbk-rust-gates
description: 用户在 Rust/Cargo 项目里的提交前与推送前质量门禁。在包含 Cargo.toml 的项目里执行 add/commit/push，或用户提到提交、推送、发版、修 CI、只测本分支相对 main 的改动、最小化测试时使用，即使没有提检查或测试。commit 前含 Rust 源码改动时运行 cargo fmt 和 clippy --fix。push 前以本分支相对 main 的变更选择最小受影响测试集，包含调用方测试，影响不明确时逐级扩大范围。不影响 Rust 构建或测试的纯文档等改动跳过门禁。非 Rust 项目不适用。
license: MIT
compatibility: 需要 Rust 工具链（cargo、rustfmt、clippy）
metadata:
  author: DBinK
  version: "0.2.0"
---

# Rust 提交/推送门禁

Rust 项目（以存在 `Cargo.toml` 为准）的硬性检查顺序。**fmt / clippy 命令原样执行。test 保留 `--all-features`，按影响范围选择包、target 和用例，不默认执行全量测试。**

## 第 0 步：判定本次改动是否涉及 Rust

commit 前检查 `git status --porcelain --untracked-files=all`，包含已暂存、未暂存和未跟踪文件。push 前无论工作区是否干净，都先确定分支累计变更：

1. 优先使用 `origin/main`，不存在时使用本地 `main`，记录所用引用及 SHA。引用已知过期时先更新。两者都不存在或无法找到共同祖先时停止并询问基线，不用当前分支的 upstream 或 `HEAD^` 代替。
2. 用 `git merge-base <main-ref> HEAD` 得到 `base`，用 `git diff --name-status --find-renames <base> HEAD` 和对应 diff 检查本分支全部变更，不只检查最后一次提交或尚未推送的提交。
3. 合并工作区状态中的改动路径检查影响，重命名同时检查新旧路径，删除也算变更。未提交改动不能作为待推送 HEAD 已通过测试的证据，push 前必须确认测试对应待推送代码状态。

在对应范围中筛选：

- `*.rs`（任意路径：`src/` 源码、`build.rs`、`examples/`、`tests/`、`benches/`）→ Rust 源码改动
- `Cargo.toml` / `Cargo.lock`（任意层级，workspace 子 crate 也算）→ 清单/依赖改动

测试夹具、快照、生成器输入、`.cargo/`、工具链或构建配置虽非 `.rs`，只要影响 Rust 构建或测试也需纳入。只有确认整个范围均不影响 Rust 的纯文档等改动，才跳过全部门禁。

## 门禁

### commit 前：fmt + clippy --fix（仅当改动含 `*.rs` 源码）

只改了 Cargo.toml/Cargo.lock、没有源码改动时，fmt / clippy 没有检查对象，直接跳过。

```bash
cargo fmt --all
cargo clippy --fix --all-targets --all-features --allow-dirty --allow-staged -- -D warnings
```

### push 前：最小受影响测试集

以第 0 步的分支累计 diff 为输入，选择能覆盖行为变化的最小测试集。main 已通过测试只说明基线通过，不代表未修改的调用方不会回归。

1. 从变更函数、类型、接口和数据入手，检查调用方与已有测试。使用仓库已有的测试映射或可靠的影响分析工具，不能只按测试文件是否修改或名称是否相似筛选。
2. 列出“变更 → 受影响行为/调用方 → 测试”的对应关系。包含新增或修改的测试、覆盖变更行为的已有单元测试、集成测试及相关 doctest。共享测试工具、夹具和快照变更覆盖所有使用者。
3. 按下表选择范围。每次扩大只到足以覆盖影响的层级，不因一个局部改动默认执行整个 workspace。
4. 执行前说明基线、选择依据和命令。使用名称筛选时，先用相同选择参数加 `-- --list` 核对匹配用例。执行后检查实际运行数量及结果，`0 tests`、全部 ignored 或仅编译成功都不算测试通过。确实没有测试时报告覆盖缺口，不宣称门禁通过。

| 影响范围                                      | 测试选择                                                                                          |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 行为和调用方均能精确定位                      | 对应 target 内的具体用例或模块筛选                                                                |
| 无法可靠缩小到用例，但能定位 target           | 该 target 全部测试                                                                                |
| crate 内共享逻辑，无法可靠缩小到 target       | 该 crate 全部测试                                                                                 |
| 公共 API、共享类型或跨 crate 行为变化         | 变更 crate 及受影响的直接、传递依赖方测试，不只测试定义所在 crate                                 |
| Cargo 清单、依赖、feature、构建脚本或配置变化 | 至少执行受影响包及依赖方的包级测试，不使用用例名筛选。无法可靠界定包集合时执行 workspace 全量测试 |
| 影响遍及 workspace，或分析后仍无法界定边界    | workspace 全量测试，并说明回退原因                                                                |

以下为命令模板，替换占位符，只执行选中的命令。包级默认测试包含 doctest，指定 `--lib` 或 `--test` 时则需单独补充相关 doctest：

```bash
cargo test -p <package> --all-features --lib <full-test-name> -- --exact
cargo test -p <package> --all-features --lib <module-filter>
cargo test -p <package> --all-features --test <target>
cargo test -p <package> --all-features --doc
cargo test -p <package> --all-features
cargo test --workspace --all-features
```

二进制等 target 使用对应的 `--bin`、`--example` 等选项。多个包可重复指定 `-p`。只有仓库明确要求全量测试、用户明确要求，或满足上表回退条件时才执行全量。

## 执行规则

1. 先做第 0 步判定。不影响 Rust 时跳过门禁，否则按 fmt → clippy --fix →（用户要求 commit）→ 受影响测试 →（用户要求 push）的顺序执行，被条件跳过的步骤直接略过。
2. `clippy --fix` 会自动改代码：改完后**重新过目 diff 再提交**，确认它没把语义改坏。
3. 任何一步失败就停下：修复后从头重跑该步，**不要带病提交**；修不了就把报错原样汇报给用户。
4. 测试通过、用户已明确要求后才能实际执行 commit / push。

## Gotchas

- `--allow-dirty --allow-staged` 是必需的：提交前工作区必然有未提交改动，不加会直接报错退出。
- `-D warnings` 让 warning 也算失败，这是有意的，不要为了通过而去掉。
- 不把“main 已通过”当作排除调用方测试的依据，也不把 Cargo 的名称筛选当作自动变更影响分析。
- push 范围始终包含相对 main 的分支累计变更。工作区只有文档改动或完全干净，不代表本分支没有 Rust 改动。
- `git status --porcelain --untracked-files=all` 用于补充未提交与未跟踪文件，不能代替分支 diff。不要只用 `git diff --cached`，它会漏掉未暂存和未跟踪文件。
- 全量测试不是默认策略。需要回退时说明具体影响或缺失的证据，不为省时取消已确定必需的测试。
- 只覆盖多语言 monorepo 的 Cargo 部分，但其他语言或资源改动若影响 Rust，也要选择相关 Rust 测试。不得削弱仓库已有的强制 CI 门禁。
