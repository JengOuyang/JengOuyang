#!/usr/bin/env python3
"""
daily_close_check.py — chart-htf 的 precheck：確認高時框 K 線真的收線且指標已算好。

為什麼需要：台北 08:00（= 00:00 UTC）是這個系統的交易日邊界，日／週／月 K 同時翻新。
CHART 在 08:08 分析高時框，但 feed-collect(08:01) 與 compute_indicators(08:03) 有沒有跑完
只靠「時間間隔」保證是不夠的——標的擴到 T2 的 20 檔之後，採集可能超過 7 分鐘。
資料沒到位就分析，等於用昨天的結構做今天的判斷。

輸出（Router 的 precheck 約定）：
  READY ...  → 觸發 chart-htf
  SKIP  ...  → 不觸發（由 chart-htf-retry 於 08:40 再試一次）
"""
from __future__ import annotations
import os, sqlite3, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("TD_DB", ROOT / "data" / "tradedesk.db"))
PARAMS = yaml.safe_load((ROOT / "shared" / "strategy_params.yaml").read_text(encoding="utf-8"))
UNIVERSE = yaml.safe_load((ROOT / "shared" / "universe.yaml").read_text(encoding="utf-8"))


def active_symbols() -> list[str]:
    out = []
    for tier in PARAMS.get("active_tiers", ["T1"]):
        t = UNIVERSE["tiers"].get(tier, {})
        out += t.get("symbols") or t.get("symbols_snapshot") or []
    return out


def main() -> int:
    now = datetime.now(timezone.utc)
    # 剛收線的那根日 K：起始時間是「昨天 00:00 UTC」
    last_daily = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    ts = int(last_daily.timestamp())
    need_weekly = now.weekday() == 0            # 週一：週 K 也剛翻
    need_monthly = now.day == 1                 # 1 號：月 K 也剛翻

    if not DB.exists():
        print(f"SKIP 資料庫不存在：{DB}")
        return 0

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    missing, suspect = [], []
    tfs = ["1d"] + (["1w"] if need_weekly else []) + (["1M"] if need_monthly else [])

    for sym in active_symbols():
        for tf in tfs:
            row = con.execute(
                "SELECT suspect FROM ohlcv WHERE symbol=? AND tf=? AND ts=?", (sym, tf, ts)
            ).fetchone()
            if row is None:
                missing.append(f"{sym}/{tf}")
            elif row[0]:
                suspect.append(f"{sym}/{tf}")
        ind = con.execute(
            "SELECT 1 FROM indicators WHERE symbol=? AND tf='1d' AND ts=? AND atr14 IS NOT NULL", (sym, ts)
        ).fetchone()
        if ind is None:
            missing.append(f"{sym}/indicators")
    con.close()

    if missing:
        print(f"SKIP 高時框資料尚未到位（{len(missing)} 項）：{', '.join(missing[:8])}"
              f"{' …' if len(missing) > 8 else ''}｜08:40 會自動重試")
        return 0
    tag = "D" + ("+W" if need_weekly else "") + ("+M" if need_monthly else "")
    warn = f"｜⚠ {len(suspect)} 項標記 SUSPECT：{', '.join(suspect[:5])}" if suspect else ""
    print(f"READY {tag} 已收線（{last_daily:%Y-%m-%d} UTC）· {len(active_symbols())} 檔標的 · 指標已算{warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
