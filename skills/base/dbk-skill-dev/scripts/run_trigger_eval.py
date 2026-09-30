#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""触发率实测示例：跑一组查询，看目标技能是否真的被加载。

这是可照抄的模板，以 pi CLI 举例。换客户端只要改两处：`run_once` 里的启动命令，
以及判定触发的那行。判定所需的信息写在下面的"判定方式"里。

用法：
    uv run run_trigger_eval.py <queries.json> <skill-name> [--runs N] [--workers N] [--only N]

    要求 Python 3.10+。用 uv 执行会按脚本内的 PEP 723 元数据自动挑解释器；用旧版
    `python3` 直接执行会明确报错退出。

可观测性
    开跑前打印规模（查询数 × runs、并发数、单次上限）；预检单独计时；运行中每 5 秒往
    stderr 打一行心跳（完成数 + 正在跑的序号及已耗时）；加 `--verbose` 时每完成一次运行
    再打一行；结尾给每条查询的平均耗时、整批总耗时与最慢单次。卡住时先看心跳，再用
    `--verbose` 的最后一行定位到具体是哪条查询。

查询集形如：

    [
      { "query": "检查一下这个 README 的文风", "should_trigger": true },
      { "query": "这个 PR 的 CI 为什么挂了", "should_trigger": false }
    ]

判定方式
    agent 会把全部技能的 name/description 注入系统提示（渐进式披露的第一层），所以
    "输出里出现 SKILL.md 路径"不能当触发标志——那样每条查询都会命中。真正的标志是
    agent 去读了技能正文：扫描 NDJSON 事件流里的 `tool_execution_start`，某次工具调用
    的参数里出现 `skills/<skill-name>/SKILL.md` 即算触发。

    换客户端时，找该客户端记录"本次加载了哪个技能"的地方，例如 omp 是输出里的
    `skill://<技能名>`，claude 是名为 `Skill` 的 tool_use，opencode 是加载日志里的
    `Loaded skill: <name>`。

退出码
    0 = 全部通过，1 = 有查询未通过，2 = 预检失败（环境不可信，直接重试即可），
    3 = 解释器低于 3.10。
    预检故障实测是间歇性的，同一命令隔一会儿重跑就能过。

运行建议
    - 需要 Python 3.10+：推荐 `uv run`，避免 `python3` 指向系统自带的旧版本；改完用
      实际要用的解释器跑一次。
    - 每条查询都是一次完整 agent 回合，耗时与机器负载强相关，`--workers` 建议 2–6。
    - 先用 `--runs 1` 粗筛，只对结果翻转的查询补 `--runs 3`。真实触发率落在 0.3–0.7
      的查询，单次运行经常落成 0 或 1，只看单次结果容易误判。
    - 不同客户端或模型的结果不可比，前后对比要固定同一个客户端。
    - 先确认客户端本身能用。整批结果全 0（连直接点名技能的那条都没触发）通常不是
      描述问题，而是客户端侧根本没产出有效响应——额度不足、鉴权失败、网络不通都会这样；
      实测遇到过 provider 返回 402 Insufficient Balance。这类失败有的会被脚本标成
      `ERR`，有的只是回一段文本、不读任何技能，看起来就像"全都没触发"。先看客户端自己的
      报错，再怀疑描述。脚本跑之前会用查询集里第一条正例做预检，不通过就中止；没有任何
      事件输出、或模型返回空响应（assistant 消息为空且无任何工具调用）的运行则标成
      `ERR` 单独计数。
"""

import argparse
import json
import platform
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 180


def _as_text(value: object) -> str:
    """把可能是 bytes 的输出片段统一成 str。"""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes | bytearray):
        return bytes(value).decode(errors="replace")
    return ""


def run_once(query: str, skill: str, timeout: int) -> str:
    """跑一条查询，返回 `yes`（加载了）/ `no`（没加载）/ `error`（本次运行没输出）。"""
    # 每次都在干净的空目录里跑，避免项目内的 AGENTS.md 等文件干扰触发判定
    workdir = tempfile.mkdtemp(prefix="skill-eval-")
    # --mode json 输出 NDJSON 事件流；--no-session 不续用本地会话历史
    cmd = ["pi", "-p", "--mode", "json", "--no-session", "--", query]
    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout + 60,
            check=False,
        )
        # 部分客户端把事件写到 stderr，两路合起来一起解析
        out = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        # 超时前已产出的输出仍可解析，别直接丢弃
        out = _as_text(exc.stdout) + _as_text(exc.stderr)
    except Exception as exc:  # noqa: BLE001 — 客户端异常退出、命令不存在等，一律算本次运行失败
        print(f"运行出错：{exc}", file=sys.stderr)
        return "error"

    # 触发标志：技能正文被读取时，其路径会出现在某次工具调用的参数里
    needle = f"skills/{skill}/SKILL.md"
    # 分别记录“有没有事件 / 有没有工具调用 / 有没有助手文本”，用于区分三种结果
    saw_event = False
    saw_tool_call = False
    saw_assistant_text = False
    for line in out.splitlines():
        # 事件流里混有非 JSON 的日志行，只解析 JSON 行
        if not line.strip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        saw_event = True
        kind = event.get("type")
        if kind == "tool_execution_start":
            saw_tool_call = True
            args = json.dumps(event.get("args") or {}, ensure_ascii=False)
            # 参数里的路径可能带转义反斜杠，去掉后再比对
            if needle in args.replace("\\", ""):
                return "yes"
        elif kind == "message_end":
            message = event.get("message") or {}
            if message.get("role") != "assistant":
                continue
            # 记录模型是否真的回了内容，用于把“空响应”和“正常但未触发”分开
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                saw_assistant_text = True
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("text"):
                        saw_assistant_text = True
    if not saw_event:
        return "error"
    if not saw_tool_call and not saw_assistant_text:
        return "error"  # 模型返回空响应，本次运行无效，别当成“未触发”
    return "no"


def _heartbeat(progress: dict[str, Any], lock: threading.Lock, interval: float = 5.0) -> threading.Event:
    """每 interval 秒往 stderr 打一行进度，避免运行时看不到卡在哪。

    progress 记录：start（起始单调时钟）、total（总运行次数）、done（已完成次数）、
    active（正在跑的 {序号: 开始时间}）。返回的 Event set 之后心跳线程退出。
    """
    stop = threading.Event()

    def loop() -> None:
        while not stop.wait(interval):
            now = time.monotonic()
            with lock:
                done = progress["done"]
                total = progress["total"]
                active = dict(progress["active"])
            running = "、".join(
                f"#{index}({now - began:.0f}s)" for index, began in sorted(active.items())
            )
            tail = f"，运行中 {running}" if running else ""
            print(f"[+{now - progress['start']:5.1f}s] 完成 {done}/{total}{tail}", file=sys.stderr)

    threading.Thread(target=loop, daemon=True).start()
    return stop


def main() -> int:
    parser = argparse.ArgumentParser(description="触发率实测示例（以 pi 为例）")
    parser.add_argument("queries", type=Path, help="查询集 JSON 文件")
    parser.add_argument("skill", help="技能名（与目录名一致）")
    parser.add_argument("--runs", type=int, default=1, help="每条查询重复次数，默认 1")
    parser.add_argument("--workers", type=int, default=4, help="并发数，默认 4")
    parser.add_argument("--only", type=int, default=None, help="只跑前 N 条查询")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT, help="单次运行上限（秒）"
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="跳过预检（默认会先验证客户端能加载技能）",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="每完成一次运行就输出一行（含序号与耗时）",
    )
    args = parser.parse_args()

    queries = json.loads(args.queries.read_text(encoding="utf-8"))
    if args.only:
        queries = queries[: args.only]

    jobs = [item["query"] for item in queries for _ in range(args.runs)]
    print(
        f"技能 {args.skill}：{len(queries)} 条查询 × {args.runs} 次 = {len(jobs)} 次运行，"
        f"并发 {args.workers}，单次上限 {args.timeout + 60}s",
        file=sys.stderr,
    )

    # 预检：先用第一条正例确认客户端能把技能喂给模型，不通过就整批中止
    positives = [item["query"] for item in queries if item["should_trigger"]]
    if positives and not args.no_preflight:
        canary = positives[0]
        print(f"预检：{canary}", file=sys.stderr)
        began = time.monotonic()
        status = run_once(canary, args.skill, args.timeout)
        took = time.monotonic() - began
        if status != "yes":
            print(
                f"预检未触发（status={status}，用时 {took:.1f}s），整批结果不可信，已中止。"
                "先看客户端自己的报错，修好再重跑；确认无误时可加 --no-preflight。",
                file=sys.stderr,
            )
            return 2
        print(f"预检通过（{took:.1f}s）", file=sys.stderr)

    start = time.monotonic()
    lock = threading.Lock()
    progress: dict[str, Any] = {"start": start, "total": len(jobs), "done": 0, "active": {}}
    stop_heartbeat = _heartbeat(progress, lock)

    def timed_run(index: int, query: str) -> tuple[int, str, float]:
        """跑一次查询，顺带记录起止时间，供心跳与统计使用。"""
        began = time.monotonic()
        with lock:
            progress["active"][index] = began
        try:
            status = run_once(query, args.skill, args.timeout)
        finally:
            with lock:
                progress["active"].pop(index, None)
                progress["done"] += 1
        return index, status, time.monotonic() - began

    results: list[tuple[str, float]] = [("error", 0.0)] * len(jobs)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(timed_run, index, query) for index, query in enumerate(jobs)]
        for future in as_completed(futures):
            index, status, took = future.result()
            results[index] = (status, took)
            if args.verbose:
                print(
                    f"[+{time.monotonic() - start:5.1f}s] #{index} {took:5.1f}s "
                    f"{status:5}  {jobs[index]}",
                    file=sys.stderr,
                )
    stop_heartbeat.set()

    # 按查询把结果切回各自的 runs 段，触发率过半即算通过
    pos_total = pos_pass = neg_total = neg_pass = errors = 0
    for index, item in enumerate(queries):
        chunk = results[index * args.runs : (index + 1) * args.runs]
        statuses = [status for status, _ in chunk]
        spent = sum(took for _, took in chunk) / len(chunk)
        should = item["should_trigger"]
        if "error" in statuses:
            errors += 1
            print(f"[ERR ] want={should!s:5} {spent:5.1f}s 本次运行没有输出  {item['query']}")
            continue
        rate = statuses.count("yes") / args.runs
        ok = rate >= 0.5 if should else rate < 0.5
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] want={should!s:5} rate={rate:.2f} {spent:5.1f}s  {item['query']}")
        if should:
            pos_total += 1
            pos_pass += ok
        else:
            neg_total += 1
            neg_pass += ok

    elapsed = time.monotonic() - start
    average = sum(took for _, took in results) / len(results) if results else 0.0
    slowest = max((took for _, took in results), default=0.0)
    print(f"\nshould-trigger: {pos_pass}/{pos_total}   should-not: {neg_pass}/{neg_total}")
    print(f"总耗时 {elapsed:.1f}s：{len(results)} 次运行，平均 {average:.1f}s，最慢 {slowest:.1f}s")
    if errors:
        print(
            f"另有 {errors} 条运行失败未计入。整批全 0 通常不是没触发，"
            "而是客户端没跑起来（额度、网络、客户端自身状态），先单独复跑确认。"
        )
    return 0 if pos_pass == pos_total and neg_pass == neg_total and not errors else 1


if __name__ == "__main__":
    # 用 platform 而不是 sys.version_info 判版本：正常入口是 `uv run`（PEP 723 已声明
    # requires-python），静态分析会按声明的最低版本把 sys.version_info 检查判成死代码。
    if tuple(int(part) for part in platform.python_version_tuple()[:2]) < (3, 10):
        print(
            f"需要 Python 3.10+，当前解释器是 {platform.python_version()}；"
            "推荐改用 `uv run` 执行本脚本。",
            file=sys.stderr,
        )
        sys.exit(3)
    sys.exit(main())
