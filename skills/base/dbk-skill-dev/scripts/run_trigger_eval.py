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
      描述问题，而是客户端在特定状态下没把技能注入系统提示——此时 agent 手里一个技能
      都没有，负例轻松通过、正例全军覆没，而且不报错。脚本跑之前会用查询集里第一条
      正例做预检，不通过就中止；没有任何事件输出、或模型返回空响应（assistant 消息
      为空且无任何工具调用）的运行则标成 `ERR` 单独计数。
"""

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_TIMEOUT = 180


def _as_text(value: object) -> str:
    """把可能是 bytes 的输出片段统一成 str。"""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode(errors="replace")
    return ""


def run_once(query: str, skill: str, timeout: int) -> str:
    """跑一条查询，返回 `yes`（加载了）/ `no`（没加载）/ `error`（本次运行没输出）。"""
    workdir = tempfile.mkdtemp(prefix="skill-eval-")
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
        out = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = _as_text(exc.stdout) + _as_text(exc.stderr)
    except Exception as exc:  # noqa: BLE001 — 客户端异常退出、命令不存在等，一律算本次运行失败
        print(f"运行出错：{exc}", file=sys.stderr)
        return "error"

    needle = f"skills/{skill}/SKILL.md"
    saw_event = False
    saw_tool_call = False
    saw_assistant_text = False
    for line in out.splitlines():
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
            if needle in args.replace("\\", ""):
                return "yes"
        elif kind == "message_end":
            message = event.get("message") or {}
            if message.get("role") != "assistant":
                continue
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
    args = parser.parse_args()

    queries = json.loads(args.queries.read_text(encoding="utf-8"))
    if args.only:
        queries = queries[: args.only]

    positives = [item["query"] for item in queries if item["should_trigger"]]
    if positives and not args.no_preflight:
        canary = positives[0]
        print(f"预检：{canary}", file=sys.stderr)
        status = run_once(canary, args.skill, args.timeout)
        if status != "yes":
            print(
                f"预检未触发（status={status}），整批结果不可信，已中止。"
                "该故障通常是间歇性的，重跑即可；反复不过再查客户端状态，"
                "或确认这条查询本身就不该触发时加 --no-preflight。",
                file=sys.stderr,
            )
            return 2

    jobs = [item["query"] for item in queries for _ in range(args.runs)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda q: run_once(q, args.skill, args.timeout), jobs))

    pos_total = pos_pass = neg_total = neg_pass = errors = 0
    for index, item in enumerate(queries):
        chunk = results[index * args.runs : (index + 1) * args.runs]
        should = item["should_trigger"]
        if "error" in chunk:
            errors += 1
            print(f"[ERR ] want={should!s:5} 本次运行没有输出  {item['query']}")
            continue
        rate = chunk.count("yes") / args.runs
        ok = rate >= 0.5 if should else rate < 0.5
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] want={should!s:5} rate={rate:.2f}  {item['query']}")
        if should:
            pos_total += 1
            pos_pass += ok
        else:
            neg_total += 1
            neg_pass += ok

    print(
        f"\nshould-trigger: {pos_pass}/{pos_total}   should-not: {neg_pass}/{neg_total}"
    )
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
