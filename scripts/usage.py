#!/usr/bin/env python3
"""
usage.py — WATCH 用量監控（每小時 program job + WATCH LLM 查詢工具）

用法：
  python scripts/usage.py --check          # 每小時排程（watch-usage, program: true）
  python scripts/usage.py --today          # 今日各 Agent 統計（供 !budget LLM 工具呼叫）
  python scripts/usage.py --window <hours> # 指定時窗統計（預設 5）

退出碼：0（Router 照貼 stdout；非零會自動觸發 BUG_REPORT）
"""
from __future__ import annotations
import argparse, json, os, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

import yaml

import td_console  # noqa: F401

ROOT = Path(os.environ.get("TD_ROOT", Path(__file__).resolve().parents[1]))
DB = Path(os.environ.get("TD_DB", ROOT / "data" / "tradedesk.db"))
PARAMS_PATH = ROOT / "shared" / "strategy_params.yaml"


def load_params() -> dict:
    try:
        return yaml.safe_load(PARAMS_PATH.read_text(encoding="utf-8")).get("llm_budget", {})
    except Exception:
        return {}


def open_db() -> sqlite3.Connection | None:
    if not DB.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        con.execute("PRAGMA query_only=1")
        con.row_factory = sqlite3.Row
        return con
    except Exception:
        return None


def fetch_usage(con: sqlite3.Connection, since_ts: int) -> list[dict]:
    """回傳 since_ts 之後的 llm_usage 紀錄。"""
    try:
        rows = con.execute(
            "SELECT agent_id, model, input_tokens, output_tokens, cost_usd_est, ts"
            "  FROM llm_usage WHERE ts >= ? ORDER BY ts",
            (since_ts,),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []  # llm_usage 表尚未建立


def compute_weight(rows: list[dict], weights: dict[str, float]) -> float:
    total = 0.0
    for r in rows:
        model = (r.get("model") or "").lower()
        w = weights.get("opus", 1.0) if "opus" in model else \
            weights.get("haiku", 0.2) if "haiku" in model else \
            weights.get("sonnet", 1.0)
        total += w
    return total


def per_agent_calls(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        aid = r.get("agent_id") or "unknown"
        counts[aid] = counts.get(aid, 0) + 1
    return counts


def mode_check(params: dict) -> int:
    now = int(time.time())
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    window_sec = 5 * 3600
    hour_sec = 3600
    since_5h = now - window_sec
    since_1h = now - hour_sec

    mw: dict[str, float] = params.get("schedule_load", {}).get("model_weight", {"opus": 3.0, "sonnet": 1.0, "haiku": 0.2})
    max_weight: float = params.get("schedule_load", {}).get("max_5h_window_weight", 6.0)
    warn_pct: float = params.get("warn_at_window_remaining_pct", 20) / 100
    per_agent_limit: dict[str, int] = params.get("per_agent_hourly_calls", {})

    con = open_db()
    if con is None:
        print(f"ℹ️ 用量檢查 {now_iso}｜資料庫尚未建立，無歷史紀錄")
        return 0

    rows_5h = fetch_usage(con, since_5h)
    rows_1h = fetch_usage(con, since_1h)
    con.close()

    weight_used = compute_weight(rows_5h, mw)
    weight_remain = max_weight - weight_used
    remain_pct = weight_remain / max_weight if max_weight > 0 else 1.0

    # 每小時各 Agent 超限檢查
    calls_1h = per_agent_calls(rows_1h)
    over_limit: list[dict] = []
    for aid, limit in per_agent_limit.items():
        actual = calls_1h.get(aid, 0)
        if actual > limit:
            over_limit.append({"agent_id": aid, "calls": actual, "limit": limit})

    # ── 全部正常 ──
    if remain_pct > warn_pct and not over_limit:
        print(
            f"✅ 用量正常 {now_iso}｜5H窗={weight_used:.1f}/{max_weight:.1f} "
            f"剩餘{remain_pct*100:.0f}%｜1H呼叫={len(rows_1h)}"
        )
        return 0

    # ── 有告警 ──
    lines: list[str] = [f"⚠️ 用量告警 {now_iso}"]
    lines.append("```")
    lines.append(f"5H窗：已用 {weight_used:.2f} / 上限 {max_weight:.1f}（剩餘 {remain_pct*100:.0f}%）")
    if over_limit:
        lines.append("")
        lines.append("Agent 超過每小時呼叫上限：")
        for o in over_limit:
            lines.append(f"  {o['agent_id']:<12} 呼叫 {o['calls']} 次 / 上限 {o['limit']}")
    lines.append("```")

    defer_agents = params.get("defer_agents_when_low", [])
    payload: dict = {
        "msg_type": "HEARTBEAT_ALERT",
        "msg_id": f"HEARTBEAT_ALERT_{now_dt.strftime('%Y%m%d_%H%M')}_usage",
        "from": "WATCH",
        "to": ["CEO"],
        "task_id": None,
        "ts": now_iso,
        "status": "INFO",
        "needs_review": remain_pct <= warn_pct,
        "payload": {
            "issue": "llm_usage_high",
            "weight_used_5h": round(weight_used, 2),
            "max_5h_weight": max_weight,
            "remaining_pct": round(remain_pct * 100, 1),
            "over_hourly_limit": over_limit,
            "defer_candidates": defer_agents if remain_pct <= warn_pct else [],
        },
    }
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
    lines.append("```")
    print("\n".join(lines))
    return 0


def mode_today(window_hours: int) -> int:
    now = int(time.time())
    now_dt = datetime.now(timezone.utc)
    since_ts = now - window_hours * 3600

    params = load_params()
    mw: dict[str, float] = params.get("schedule_load", {}).get("model_weight", {"opus": 3.0, "sonnet": 1.0, "haiku": 0.2})
    max_weight: float = params.get("schedule_load", {}).get("max_5h_window_weight", 6.0)
    per_agent_limit: dict[str, int] = params.get("per_agent_hourly_calls", {})

    con = open_db()
    if con is None:
        print(json.dumps({"error": "資料庫不存在", "db": str(DB)}, ensure_ascii=False))
        return 1

    rows = fetch_usage(con, since_ts)
    con.close()

    calls = per_agent_calls(rows)
    total_weight = compute_weight(rows, mw)

    # 逐 Agent 統計
    agent_stats: list[dict] = []
    for aid in sorted(set(list(calls.keys()) + list(per_agent_limit.keys()))):
        n = calls.get(aid, 0)
        limit = per_agent_limit.get(aid)
        agent_rows = [r for r in rows if r.get("agent_id") == aid]
        cost = sum(r.get("cost_usd_est") or 0 for r in agent_rows)
        agent_stats.append({
            "agent_id": aid,
            "calls": n,
            "hourly_limit": limit,
            "cost_usd_est": round(cost, 4),
        })

    result = {
        "window_hours": window_hours,
        "as_of": now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_calls": len(rows),
        "total_weight_5h_equiv": round(total_weight, 2),
        "max_5h_window_weight": max_weight,
        "remaining_pct": round((max_weight - total_weight) / max_weight * 100, 1) if max_weight else None,
        "per_agent": agent_stats,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="WATCH 用量監控")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="每小時排程模式")
    group.add_argument("--today", action="store_true", help="今日統計（JSON 輸出）")
    parser.add_argument("--window", type=int, default=5, help="統計時窗小時數（--today 用）")
    args = parser.parse_args()

    params = load_params()

    if args.check:
        return mode_check(params)
    elif args.today:
        return mode_today(args.window)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
