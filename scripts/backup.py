#!/usr/bin/env python3
"""backup.py — 每日定時備份入口；讀 BACKUP_DEST 環境變數後委派給 backup_mirror.py。

環境變數：
    BACKUP_DEST  備份目的地路徑（另一顆碟 / 雲端同步資料夾）
                 未設定 → exit 2 並印說明；空字串視同未設定。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    dest = os.environ.get("BACKUP_DEST", "").strip()
    if not dest:
        print(
            "❌ BACKUP_DEST 未設定。\n"
            "   請在 router/.env 加入：BACKUP_DEST=<備份目的地目錄>\n"
            "   例如：BACKUP_DEST=D:/backup/trade-desk"
        )
        return 2

    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "backup_mirror.py"), "--to", dest],
        cwd=ROOT,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
