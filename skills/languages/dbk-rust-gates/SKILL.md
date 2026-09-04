---
name: dbk-rust-gates
description: 用户在 Rust/Cargo 项目里的提交前与推送前质量门禁，仅当改动涉及 Rust 相关文件时生效。在包含 Cargo.toml 的项目里执行 add/commit/push、或用户提到提交、推送、发版、修 CI 时使用——即使用户没有提"检查"或"测试"。先判定改动是否命中 Rust 源码（*.rs）或 Cargo.toml/Cargo.lock：只改了文档、CI、配置等非 Rust 文件就跳过全部门禁，正常 commit/push。命中的改动才需要门禁：含源码改动时 commit 前必须先跑 cargo fmt 和 clippy --fix；push 前必须先跑全量 cargo test。非 Rust 项目不适用。
license: MIT
compatibility: 需要 Rust 工具链（cargo、rustfmt、clippy）
metadata:
  author: DBinK
  version: "0.2.0"
---

# Rust 提交/推送门禁

Rust 项目（以存在 `Cargo.toml` 为准）的硬性检查顺序。**门禁命令原样执行，不要增删参数。**

## 第 0 步：判定本次改动是否涉及 Rust

先确认要提交/推送的改动里有没有 Rust 相关文件，**没有就直接跳过全部门禁**，不必跑任何 cargo 检查。

看 `git status --porcelain` 的输出（含未暂存与未跟踪文件），逐行筛选：

- `*.rs`（任意路径：`src/` 源码、`build.rs`、`examples/`、`tests/`、`benches/`）→ Rust 源码改动
- `Cargo.toml` / `Cargo.lock`（任意层级，workspace 子 crate 也算）→ 清单/依赖改动

命中任一即视为"涉及 Rust"。工作区完全干净、只剩 push 时，判定对象换成待推送提交：`git diff --name-only <base>..HEAD`（base 用 `git merge-base @{u} HEAD`；没有 upstream 就用 `HEAD^`）。

## 门禁

### commit 前：fmt + clippy --fix（仅当改动含 `*.rs` 源码）

只改了 Cargo.toml/Cargo.lock、没有源码改动时，fmt / clippy 没有检查对象，直接跳过。

```bash
cargo fmt --all
cargo clippy --fix --all-targets --all-features --allow-dirty --allow-staged -- -D warnings
```

### push 前：全量测试（只要命中就必跑）

只改了 Cargo.toml/Cargo.lock 也必须跑：依赖树变了，要验证仍能编译、测试通过。

```bash
cargo test --all-features
```

## 执行规则

1. 先做第 0 步判定：未命中 Rust 相关文件 → 跳过全部门禁，正常 commit / push；命中 → 按 fmt → clippy --fix →（用户要求 commit）→ test →（用户要求 push）的顺序执行，被条件跳过的步骤直接略过。
2. `clippy --fix` 会自动改代码：改完后**重新过目 diff 再提交**，确认它没把语义改坏。
3. 任何一步失败就停下：修复后从头重跑该步，**不要带病提交**；修不了就把报错原样汇报给用户。
4. 测试通过、用户已明确要求后才能实际执行 commit / push。

## Gotchas

- `--allow-dirty --allow-staged` 是必需的：提交前工作区必然有未提交改动，不加会直接报错退出。
- `-D warnings` 让 warning 也算失败，这是有意的，不要为了通过而去掉。
- 首次在该项目跑全量测试可能很慢，属正常，不要中途取消。
- 判定必须用 `git status --porcelain` 而不是 `git diff --cached`：未暂存、未跟踪的新 `.rs` 文件后者会漏判；也不要用 `git diff --name-only HEAD`，它不含未跟踪文件。
- 只对 Rust 项目生效；多语言 monorepo 里只覆盖 Cargo 部分：改动里混着 `.rs` / Cargo 文件与其他语言文件时按"涉及 Rust"处理，整个门禁照跑，不要只挑 Rust 子集检查。
