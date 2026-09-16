#!/usr/bin/env python3
"""install_git_hooks.py — 裝上本機 git 鉤子（私有庫在 GitHub Free 沒有伺服器端防護）。

裝三個：
  pre-commit  金鑰掃描 + lint（擋住「把金鑰或壞掉的設定 commit 進去」）
  pre-push    完整驗證（切片雜湊 + 隔離 + 文件宣稱 + pytest）
  post-commit 提醒鏡像備份（git 不是備份，見 docs/13_GITHUB.md）

用法：python scripts/install_git_hooks.py
移除：python scripts/install_git_hooks.py --uninstall
"""
from __future__ import annotations

import stat
import sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".git" / "hooks"

# 鉤子由 git 執行，不是由你的 PowerShell 執行——venv **不會**是啟動狀態。
# 直接寫 `python` 會用到系統的那支（可能沒裝相依套件，或根本不存在），
# 鉤子就會以「找不到模組」失敗，看起來像專案壞了。先解析出正確的直譯器。
PICK_PY = """PY=python
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"
[ -x ".venv/Scripts/python.exe" ] && PY=".venv/Scripts/python.exe"
"""

PRE_COMMIT = f"""#!/bin/sh
# TRADE-DESK pre-commit：金鑰是不可逆的，先擋金鑰再擋設定漂移
{PICK_PY}
"$PY" scripts/check_secrets.py || exit 1
"$PY" scripts/lint_agents.py   || exit 1
"""

PRE_PUSH = f"""#!/bin/sh
# TRADE-DESK pre-push：推上去之前跑完整驗證（GitHub Actions 會再跑一次，但本機先知道比較便宜）
{PICK_PY}
"$PY" scripts/build_context.py --verify || exit 1
"$PY" scripts/verify_isolation.py       || exit 1
"$PY" scripts/verify_docs_claims.py     || exit 1
"$PY" -m pytest tests -q                || exit 1
"""

POST_COMMIT = """#!/bin/sh
# TRADE-DESK post-commit：提醒鏡像備份
echo "提醒：GitHub 是遠端副本，不是備份。每週跑 scripts/backup_mirror.py（見 docs/13_GITHUB.md）"
"""

FILES = {"pre-commit": PRE_COMMIT, "pre-push": PRE_PUSH, "post-commit": POST_COMMIT}


def main() -> int:
    if not HOOKS.parent.exists():
        print("這個目錄還不是 git 版本庫——先跑 `git init`（見 docs/DAY0_RUNBOOK.md 第 3 步）")
        return 1
    HOOKS.mkdir(parents=True, exist_ok=True)

    if "--uninstall" in sys.argv:
        for name in FILES:
            (HOOKS / name).unlink(missing_ok=True)
        print("已移除 3 個 git 鉤子")
        return 0

    for name, body in FILES.items():
        f = HOOKS / name
        f.write_text(body, encoding="utf-8", newline="\n")
        f.chmod(f.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"已安裝 .git/hooks/{name}")
    print("\nWindows 原生 git 也會執行這些 sh 腳本（Git for Windows 自帶 sh）。")
    print("要臨時跳過：git commit --no-verify（金鑰那道請不要跳過）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
