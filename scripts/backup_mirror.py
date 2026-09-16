#!/usr/bin/env python3
"""backup_mirror.py — 3-2-1 備份的第二、三份副本。

為什麼 GitHub 不算備份：
    帳號被停權、倉庫被誤刪、force-push 覆蓋、或 GitHub 本身出事時，
    「遠端副本」會跟著一起消失。git 的分散式特性讓每個 clone 都是完整歷史，
    但前提是你真的有另一份 clone。

這支程式做三件事：
  1. `git bundle` 打包整個歷史成單一檔案（可放雲端硬碟 / 隨身碟）
  2. 鏡像 clone 到另一個實體位置（--to）
  3. 匯出「不進版控但不能丟」的東西：router/.env 的**鍵名清單**（不含值）、
     資料庫 schema、以及 data/ 的檔案清單與大小（資料本身另有 db 備份策略）

用法：
    python scripts/backup_mirror.py --to D:/backup/trade-desk
    python scripts/backup_mirror.py --to /mnt/d/backup/trade-desk --bundle-only
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=child_env())
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, help="備份目的地目錄（另一顆碟 / 雲端同步資料夾）")
    ap.add_argument("--bundle-only", action="store_true", help="只做 bundle，不做鏡像 clone")
    a = ap.parse_args()

    dest = Path(a.to).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d")

    # 0 先確認工作區乾淨——備份一個半成品沒有意義
    rc, out = run(["git", "status", "--porcelain"])
    if out:
        print("⚠️ 工作區有未 commit 的變更，備份的是最後一次 commit 的狀態：")
        print("   " + out.replace("\n", "\n   ")[:400])

    # 1 bundle：單一檔案、含全部分支與標籤
    bundle = dest / f"trade-desk-{stamp}.bundle"
    rc, out = run(["git", "bundle", "create", str(bundle), "--all"])
    if rc != 0:
        print(f"bundle 失敗：{out}"); return 1
    print(f"✅ bundle：{bundle}（{bundle.stat().st_size/1_048_576:.1f} MB）")
    print(f"   還原方式：git clone {bundle.name} trade-desk")

    # 2 鏡像 clone
    if not a.bundle_only:
        mirror = dest / "trade-desk.git"
        if mirror.exists():
            rc, out = run(["git", "remote", "update", "--prune"], cwd=mirror)
        else:
            rc, out = run(["git", "clone", "--mirror", str(ROOT), str(mirror)])
        print(("✅ 鏡像：" if rc == 0 else "❌ 鏡像失敗：") + (str(mirror) if rc == 0 else out))

    # 3 不進版控但不能丟的東西
    notes = [f"# TRADE-DESK 備份附註 {stamp}", ""]
    env = ROOT / "router" / ".env"
    if env.exists():
        keys = [l.split("=")[0].strip() for l in env.read_text(encoding="utf-8").splitlines()
                if "=" in l and not l.strip().startswith("#")]
        notes += ["## router/.env 需要的鍵（**值不備份，值請放密碼管理器**）", ""] + [f"- {k}" for k in keys] + [""]
    db = ROOT / "data" / "tradedesk.db"
    if db.exists():
        notes += [f"## 資料庫", f"- data/tradedesk.db　{db.stat().st_size/1_048_576:.1f} MB",
                  "- 資料庫不進 git；請另外用 `sqlite3 data/tradedesk.db \".backup 'x.db'\"` 備份", ""]
    (dest / f"RESTORE-{stamp}.md").write_text("\n".join(notes), encoding="utf-8")
    print(f"✅ 附註：{dest / f'RESTORE-{stamp}.md'}")

    print("\n3-2-1 檢查：這是第 2 份（本機另一個位置）與第 3 份（若 --to 指向雲端同步資料夾）。")
    print("第 1 份是工作目錄，GitHub 遠端是額外的第 4 份——它是協作與 CI 用的，不是備份。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
