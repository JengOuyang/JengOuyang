#!/usr/bin/env python3
"""
heartbeat_check.py — WATCH 心跳監控（每 15 分鐘，program: true）

從 router_state.db 讀取各 Agent 的最後心跳時間，
對「高頻 program-job」Agent（間隔 ≤ 30 分鐘）嚴格驗證；
其他 Agent 只回報最後見到的時間（資訊性）。

輸出（Router 把 stdout 貼到 CH_AGENT_HEALTH）：
  - 全部正常：一行摘要
  - 有逾時：狀態表 + HEARTBEAT_ALERT JSON
退出碼：0（Router 把 stdout 照貼；非 0 會自動觸發 BUG_REPORT）
"""
from __future__ import annotations
import json, os, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(os.environ.get("TD_ROOT", Path(__file__).resolve().parents[1]))
STATE_DB = ROOT / "router" / "router_state.db"
AGENTS_CFG_PATH = ROOT / "router" / "agents.yaml"
SCHED_PATH = ROOT / "router" / "scheduler.yaml"

# 只有間隔 ≤ 這個秒數的 program-job 才列入嚴格監控
STRICT_THRESHOLD_SEC = 30 * 60
# 超過 interval * ALERT_MULTIPLIER 才發告警（容忍排程抖動）
ALERT_MULTIPLIER = 2.5


def _cron_min_interval(cron: str) -> int | None:
    """把 cron 字串轉成最小間隔秒數；只處理 */N 與固定 minute 欄位。"""
    parts = cron.split()
    if len(parts) != 5:
        return None
    minute = parts[0]
    if minute.startswith("*/"):
        try:
            return int(minute[2:]) * 60
        except ValueError:
            return None
    # 每小時某個固定分鐘 → 3600 秒
    hour = parts[1]
    if hour == "*":
        return 3600
    return None  # 每日/每週/固定時點 → 不算嚴格心跳


def build_interval_map() -> dict[str, int]:
    """回傳各 agent 最短 program-job 間隔（秒）；只包含 program: true 的任務。"""
    try:
        sched = yaml.safe_load(SCHED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    result: dict[str, int] = {}
    for job in sched.get("jobs", []):
        if not job.get("program"):
            continue
        aid = job["agent"]
        secs = _cron_min_interval(job.get("cron", ""))
        if secs is None:
            continue
        if aid not in result or secs < result[aid]:
            result[aid] = secs
    return result


def load_heartbeats() -> dict[str, dict]:
    """從 router_state.db 讀最後心跳；DB 不存在時回空字典。"""
    if not STATE_DB.exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT agent_id, ts, task, status, error FROM heartbeat"
        ).fetchall()
        con.close()
        return {
            r[0]: {"ts": r[1], "task": r[2], "status": r[3], "error": r[4]}
            for r in rows
        }
    except Exception:
        return {}


def load_agent_names() -> dict[str, str]:
    """回傳 {agent_id: display_name}。"""
    try:
        cfg = yaml.safe_load(AGENTS_CFG_PATH.read_text(encoding="utf-8"))
        return {aid: a.get("name", aid) for aid, a in cfg.get("agents", {}).items()}
    except Exception:
        return {}


def main() -> int:
    now = time.time()
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    intervals = build_interval_map()
    heartbeats = load_heartbeats()
    names = load_agent_names()

    stale: list[dict] = []
    table_rows: list[tuple[str, str, str, str]] = []

    for aid in sorted(intervals):
        interval_sec = intervals[aid]
        is_strict = interval_sec <= STRICT_THRESHOLD_SEC
        hb = heartbeats.get(aid)

        if hb is None:
            last_seen_str = "從未"
            elapsed_sec = None
            emoji = "⚠️" if is_strict else "❓"
            if is_strict:
                stale.append({
                    "agent_id": aid,
                    "last_seen": None,
                    "elapsed_sec": None,
                    "expected_interval_sec": interval_sec,
                })
        else:
            elapsed_sec = now - hb["ts"]
            last_dt = datetime.fromtimestamp(hb["ts"], tz=timezone.utc)
            last_seen_str = last_dt.strftime("%H:%M:%S")
            threshold = interval_sec * ALERT_MULTIPLIER
            if is_strict and elapsed_sec > threshold:
                emoji = "❌"
                stale.append({
                    "agent_id": aid,
                    "last_seen": last_dt.isoformat(),
                    "elapsed_sec": round(elapsed_sec),
                    "expected_interval_sec": interval_sec,
                })
            else:
                emoji = "✅"

        table_rows.append((
            names.get(aid, aid),
            last_seen_str,
            f"{interval_sec // 60}m",
            emoji,
        ))

    if not stale:
        # 全部正常：只輸出一行，不佔頻道版面
        ok_agents = ", ".join(names.get(a, a) for a in sorted(intervals))
        print(f"✅ 心跳正常 {now_iso}｜{len(intervals)} 個程式 Agent：{ok_agents}")
        return 0

    # 有逾時：輸出表格 + JSON
    lines: list[str] = [f"⚠️ 心跳告警 {now_iso}"]
    lines.append("```")
    header = f"{'Agent':<14} {'最後心跳(UTC)':<16} {'間隔':<6} 狀態"
    lines.append(header)
    lines.append("-" * len(header))
    for name, ls, iv, em in table_rows:
        lines.append(f"{name:<14} {ls:<16} {iv:<6} {em}")
    lines.append("```")

    payload = {
        "msg_type": "HEARTBEAT_ALERT",
        "msg_id": f"HEARTBEAT_ALERT_{now_dt.strftime('%Y%m%d_%H%M')}_stale",
        "from": "WATCH",
        "to": ["CEO"],
        "task_id": None,
        "ts": now_iso,
        "status": "INFO",
        "needs_review": False,
        "payload": {"stale_agents": stale},
    }
    lines.append(f"\n{len(stale)} 個 Agent 心跳逾時，請 CEO 確認。")
    lines.append("```json")
    lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
    lines.append("```")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
