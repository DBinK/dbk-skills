#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""用 acpx 跑技能触发实测，判断目标技能是否被真正读取。

和同目录 run_trigger_eval.py 的区别：那个直接调客户端 CLI 再 grep 文本，这个走
Agent Client Protocol 拿结构化事件，判定依据只有一个——有没有某次工具调用读取了
<技能名>/SKILL.md。好处是不受系统提示里注入的技能清单干扰（清单里就带 SKILL.md
路径，文本 grep 会把每条查询都判成触发），还能顺带看到每次运行调了哪些工具。

用法：

    uv run skills/base/dbk-skill-dev/scripts/run_trigger_eval_acpx.py \
        skills/base/dbk-agent-rules/evals/trigger-queries.json dbk-agent-rules

常用参数：--agent（默认 pi）、--runs、--workers、--cwd、--timeout、--verbose。

关于 acpx（0.19.5 实测通过）：

- 用 `npx -y acpx@latest` 调用，不要求全局安装，也不会把版本钉死。
- acpx 还是 pre-1.0，CLI 会变。跑不通先看 `npx -y acpx@latest --help`，
  再看官方文档 https://acpx.sh/ ，仓库里的 docs/CLI.md 与 docs/agents.md 是权威来源。
- 坑一：--format / --approve-reads / --cwd / --timeout 都是**全局选项**，
  必须写在子命令前面。`acpx exec --format json` 会报 unknown option，
  正确写法是 `acpx --format json pi exec "<prompt>"`。
- 坑二：agent 本身是子命令（`acpx <agent> exec "<prompt>"`）。内置 profile 见
  docs/agents.md，支持 pi / openclaw / codex / claude 等，也能用
  `--agent '<命令>'` 接自定义 ACP server。
- 坑三：acpx 会把 npm notice 打到 stderr。解析时只认以 `{` 开头的 NDJSON 行，
  加 --json-strict 可以少些噪音。
- 坑四：`--approve-all` 会连写入一起放行。测技能触发只需要读权限，这里固定用
  `--approve-reads --non-interactive-permissions deny`，读自动放行、写一律拒绝。
- 坑六：**别在批量运行里带 `@latest`**。实测本机 `npx -y acpx@latest --version`
  要 31-38s，不带 `@latest` 只要 1.17s，直接调 npx 缓存里的二进制是 0.11s。
  所以预热阶段跑一次 `acpx@latest` 刷新缓存，批量运行统一用不带版本的形式，
  一整轮 21 条从 ~400s 降到百秒级。想换回每次都查最新版，把 ACPX 改回 ACPX_LATEST 即可。
- 坑五：npx 缓存是冷的、又同时起多个进程时会互相抢下载，个别运行会直接崩
  （exit=1，stderr 里只剩一行 Node.js 版本号）。所以脚本开跑前先做一次预热运行，
  再放并发，用 `--no-preflight` 可以跳过。

判定用的 ACP 事件形状（--format json 输出，NDJSON，每行一个 JSON-RPC 消息）：

    {"jsonrpc":"2.0","method":"session/update","params":{"update":{
        "sessionUpdate":"tool_call",
        "title":"read","kind":"read","status":"pending",
        "locations":[{"path":".../skills/dbk-agent-rules/SKILL.md"}],
        "rawInput":{"path":".../skills/dbk-agent-rules/SKILL.md"}}}}

所以判据是：任意 tool_call / tool_call_update 事件的 locations[].path 或
rawInput 里的路径，末两段为 `<技能名>/SKILL.md`。判不出事件就当 ERR 处理，
不算触发失败——客户端没跑起来和「没触发」是两回事。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import PurePath

# 批量运行不带 @latest：它会强制查 registry 的 dist-tag，实测本机要 31-38s，
# 不带则只要 1.17s（命中同一个 npx 缓存）。版本新鲜度交给预热阶段处理。
ACPX = ["npx", "-y", "acpx"]
ACPX_LATEST = ["npx", "-y", "acpx@latest"]
PATH_KEYS = ("path", "file_path", "filePath", "filename")
TOOL_TITLES = {"skill", "load skill", "use skill", "read skill"}


def build_cmd(agent: str, prompt: str, cwd: str, timeout: int, prefix: list[str] | None = None) -> list[str]:
    """拼 acpx 命令行。全局选项必须排在 agent 子命令之前。"""
    return [
        *(prefix or ACPX),
        "--format", "json",
        "--json-strict",
        "--approve-reads",
        "--non-interactive-permissions", "deny",
        "--cwd", cwd,
        "--timeout", str(timeout),
        agent,
        "exec",
        prompt,
    ]


def iter_updates(stdout: str):
    """从 acpx 的 NDJSON 输出里取出 session/update 的 update 对象。"""
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("method") != "session/update":
            continue
        update = (msg.get("params") or {}).get("update")
        if isinstance(update, dict):
            yield update


def candidate_paths(update: dict) -> list[str]:
    paths: list[str] = []
    for loc in update.get("locations") or []:
        if isinstance(loc, dict) and isinstance(loc.get("path"), str):
            paths.append(loc["path"])
    raw = update.get("rawInput")
    if isinstance(raw, dict):
        for key in PATH_KEYS:
            value = raw.get(key)
            if isinstance(value, str):
                paths.append(value)
    return paths


def is_skill_read(update: dict, skill: str) -> bool:
    """这次工具调用是不是读了目标技能的正文。"""
    for path in candidate_paths(update):
        parts = PurePath(path).parts
        if len(parts) >= 2 and parts[-1] == "SKILL.md" and parts[-2] == skill:
            return True
    # 兜底：客户端可能用专门的 skill 工具，rawInput 里只带技能名。
    # 这里已经是工具调用事件，不会撞上系统提示里的技能清单。
    raw = json.dumps(update.get("rawInput") or {}, ensure_ascii=False)
    title = str(update.get("title") or "").strip().lower()
    if skill in raw and ("SKILL.md" in raw or title in TOOL_TITLES):
        return True
    return False


def run_once(agent: str, skill: str, prompt: str, cwd: str, timeout: int):
    """跑一次。返回 (状态, 是否触发, 工具调用标题, 备注)。"""
    cmd = build_cmd(agent, prompt, cwd, timeout)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
    except FileNotFoundError:
        return "error", False, [], "找不到 npx，先确认 Node.js 可用"
    except subprocess.TimeoutExpired:
        return "error", False, [], f"acpx 超时（{timeout + 60}s）"

    updates = list(iter_updates(proc.stdout))
    if not updates:
        reason = summarize_failure(proc)
        return "error", False, [], f"没解析到 ACP 事件（exit={proc.returncode}）：{reason}"

    hit = any(is_skill_read(u, skill) for u in updates)
    titles = [
        str(u.get("title") or "?")
        for u in updates
        if str(u.get("sessionUpdate", "")).startswith("tool_call")
    ]
    return "ok", hit, titles, ""


def summarize_failure(proc: subprocess.CompletedProcess) -> str:
    """从 stderr 里挑一句能读的报错。acpx 失败时末尾往往只剩 Node 版本号。"""
    text = proc.stderr or proc.stdout or ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        low = line.lower()
        if "error" in low or "cannot" in low or "not found" in low or "unknown option" in low:
            return line[:160]
    return lines[-1][:160] if lines else "没有任何输出"


def preflight(agent: str, cwd: str, timeout: int) -> tuple[bool, str]:
    """开跑前先热一次 npx 缓存，顺带确认 agent 真的能起来。

    实测过并发抢冷缓存的坑：同时起 3 个 `npx acpx@latest`，个别进程会直接崩，
    stderr 里只剩一行 Node.js 版本号，看起来像「没触发」，其实只是没跑起来。
    """
    def refresh() -> None:
        try:
            subprocess.run([*ACPX_LATEST, "--version"], capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def versions() -> tuple[str, str]:
        """(缓存里的版本, registry 上的最新版)。查 dist-tag 实测只要 0.3s。"""
        have = latest = ""
        try:
            proc = subprocess.run([*ACPX, "--version"], capture_output=True, text=True, timeout=120)
            have = proc.stdout.strip() if proc.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            proc = subprocess.run(["npm", "view", "acpx", "version"], capture_output=True, text=True, timeout=60)
            latest = proc.stdout.strip() if proc.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            pass
        return have, latest

    # 只在缓存落后时才付 @latest 的重装代价（实测 30s 以上）。版本一致就直接用缓存，
    # 预热从 46s 降到几秒。拿不到最新版（离线等）时沿用缓存，不阻断实测。
    have, latest = versions()
    if not have or (latest and have != latest):
        refresh()
        have, latest = versions()
    if not have:
        return False, "npx 缓存里的 acpx 不可用，刷新后仍拿不到版本号"

    cmd = build_cmd(agent, "回复两个字：收到", cwd, timeout)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
    except FileNotFoundError:
        return False, "找不到 npx，先确认 Node.js 可用"
    except subprocess.TimeoutExpired:
        return False, f"预热超时（{timeout + 60}s）"
    updates = list(iter_updates(proc.stdout))
    if not updates:
        return False, f"预热没拿到 ACP 事件（exit={proc.returncode}）：{summarize_failure(proc)}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="用 acpx 做技能触发实测")
    parser.add_argument("queries", help="查询集 JSON，形如 [{\"query\":..., \"should_trigger\":true}]")
    parser.add_argument("skill", help="目标技能名，例如 dbk-agent-rules")
    parser.add_argument("--agent", default="pi", help="acpx 的 agent profile，默认 pi")
    parser.add_argument("--runs", type=int, default=1, help="每条查询跑几次，默认 1")
    parser.add_argument("--workers", type=int, default=4, help="并发数，默认 4")
    parser.add_argument("--cwd", default=".", help="agent 的工作目录，默认当前目录")
    parser.add_argument("--timeout", type=int, default=240, help="单次等待上限秒数，默认 240")
    parser.add_argument("--verbose", action="store_true", help="逐条打印工具调用")
    parser.add_argument("--no-preflight", action="store_true", help="跳过预热运行")
    args = parser.parse_args()

    with open(args.queries, encoding="utf-8") as handle:
        queries = json.load(handle)
    total_runs = len(queries) * args.runs
    print(
        f"技能 {args.skill}：{len(queries)} 条查询 × {args.runs} 次 = {total_runs} 次运行，"
        f"agent={args.agent}，并发 {args.workers}"
    )

    if not args.no_preflight:
        started = time.time()
        ok, note = preflight(args.agent, args.cwd, min(args.timeout, 120))
        if not ok:
            print(f"预热失败，整批结果不可信，已中止：{note}")
            print("先确认 agent 能起来（npx -y acpx@latest --help、agent 是否已登录），再重跑。")
            return 2
        print(f"预热通过（{time.time() - started:.1f}s）")

    jobs = [(idx, run) for idx in range(len(queries)) for run in range(args.runs)]
    hits: list[list[bool]] = [[] for _ in queries]
    errors: list[str] = []
    titles_seen: dict[int, list[str]] = {}
    started = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                run_once, args.agent, args.skill, queries[idx]["query"], args.cwd, args.timeout
            ): idx
            for idx, _ in jobs
        }
        for future in as_completed(futures):
            idx = futures[future]
            status, hit, titles, note = future.result()
            if status == "error":
                errors.append(f"{queries[idx]['query']}：{note}")
            else:
                hits[idx].append(hit)
                if titles:
                    titles_seen.setdefault(idx, []).extend(titles)

    passed = 0
    for idx, item in enumerate(queries):
        want = bool(item.get("should_trigger"))
        got = hits[idx]
        rate = (sum(got) / len(got)) if got else 0.0
        ok = bool(got) and (rate >= 0.5) == want
        passed += ok
        mark = "PASS" if ok else ("ERR " if not got else "FAIL")
        rate_text = f"{rate:.2f}" if got else " -- "
        print(f"[{mark}] want={str(want):<5} rate={rate_text}  {item['query']}")
        if args.verbose and titles_seen.get(idx):
            print("        工具调用: " + " | ".join(titles_seen[idx][:8]))

    positives = [i for i, q in enumerate(queries) if q.get("should_trigger")]
    negatives = [i for i, q in enumerate(queries) if not q.get("should_trigger")]

    def score(indexes: list[int]) -> str:
        good = sum(1 for i in indexes if bool(hits[i]) and (sum(hits[i]) / len(hits[i]) >= 0.5) == bool(queries[i].get("should_trigger")))
        return f"{good}/{len(indexes)}"

    print(f"\nshould-trigger: {score(positives)}   should-not: {score(negatives)}")
    print(f"总耗时 {time.time() - started:.1f}s")
    if errors:
        print(f"\n另有 {len(errors)} 次运行失败未计入：")
        for note in errors[:8]:
            print(f"  - {note}")
        print("  客户端没跑起来和「没触发」是两回事，先排查再下结论。")
    return 0 if not errors and passed == len(queries) else 1


if __name__ == "__main__":
    sys.exit(main())
