---
name: dbk-rust-gates
description: 用户在 Rust/Cargo 项目里的提交前与推送前质量门禁。只要要在包含 Cargo.toml 的项目里执行 add/commit/push、或用户提到提交、推送、发版、修 CI，就必须先按本技能跑完对应检查再行动——即使用户没有提"检查"或"测试"。包含两条硬性门禁：commit 前必须先跑 cargo fmt 和 clippy --fix；push 前必须先跑全量 cargo test。非 Rust 项目不适用。
---

# Rust 提交/推送门禁

Rust 项目（以存在 `Cargo.toml` 为准）的硬性检查顺序。**命令原样执行，不要增删参数。**

## 门禁

### commit 前必跑（格式化 + lint 自动修复）

```bash
cargo fmt --all
cargo clippy --fix --all-targets --all-features --allow-dirty --allow-staged -- -D warnings
```

### push 前必跑（全量测试）

```bash
cargo test --all-features
```

## 执行规则

1. 按顺序跑：fmt → clippy --fix → （用户要求 commit）→ test → （用户要求 push）。
2. `clippy --fix` 会自动改代码：改完后**重新过目 diff 再提交**，确认它没把语义改坏。
3. 任何一步失败就停下：修复后从头重跑该步，**不要带病提交**；修不了就把报错原样汇报给用户。
4. 测试通过、用户已明确要求后才能实际执行 commit / push。

## Gotchas

- `--allow-dirty --allow-staged` 是必需的：提交前工作区必然有未提交改动，不加会直接报错退出。
- `-D warnings` 让 warning 也算失败，这是有意的，不要为了通过而去掉。
- 首次在该项目跑全量测试可能很慢，属正常，不要中途取消。
- 只对 Rust 项目生效；多语言 monorepo 里只覆盖 Cargo 部分。
