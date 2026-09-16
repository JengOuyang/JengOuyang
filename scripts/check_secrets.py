#!/usr/bin/env python3
"""check_secrets.py — 推上 GitHub 之前的本地金鑰閘門。

為什麼要自己寫：
    GitHub 的 secret scanning / push protection **對私有庫要付費**
    （Free 方案只有公開庫免費；私有庫需要 GitHub Secret Protection）。
    這個專案是私有庫 + 免費方案，所以伺服器端沒有這道防線——
    唯一的機會是在 commit 之前於本機擋下來。
    安裝：`python scripts/install_git_hooks.py`（裝成 pre-commit）。

    金鑰一旦推上去就算刪掉 commit 也要當作已外洩：必須去交易所 / Discord 撤銷重發。
    這支程式的目的就是讓那件事不要發生。

用法：
    python scripts/check_secrets.py                  # 掃已 staged 的檔（pre-commit 用）
    python scripts/check_secrets.py --all            # 掃整個工作區（定期體檢）
    python scripts/check_secrets.py --history        # 掃全部 commit 的歷史（搬家到 GitHub 前跑一次）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_paths import EXCLUDED_DIRS
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]

# 樣式取名以「誤判可接受、漏判不可接受」為原則
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Discord Bot Token", re.compile(r"[MNO][A-Za-z\d_-]{23,27}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI API Key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack Token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Notion Token", re.compile(r"(?:secret_|ntn_)[A-Za-z0-9]{35,}")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    # Bitget / 一般交易所：key 名稱旁邊出現像 key 的長字串
    ("Exchange Secret", re.compile(
        r"(?i)(api[_-]?secret|api[_-]?key|passphrase|secret[_-]?key)\s*[:=]\s*[\"']([A-Za-z0-9/+_\-]{20,})[\"']")),
    ("Generic Bearer", re.compile(r"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._\-]{20,}")),
]

# 範例檔與本程式自身一定會「長得像」有金鑰
SKIP_SUFFIX = (".example", ".sample", ".template")
SKIP_NAMES = {"check_secrets.py"}
# 佔位字樣：這些不是真金鑰
PLACEHOLDER = re.compile(r"(?i)(your[_-]?|xxx|placeholder|changeme|example|<.*>|\.\.\.|TODO)")
# 明示豁免：測試需要「長得完全像真的」的假金鑰，否則就測不到掃描器有沒有效。
# 必須逐行標記——不是整個檔案豁免，這樣新增的真金鑰仍然會被抓到。
ALLOW = re.compile(r"check_secrets:\s*allow")


def scan_text(name: str, text: str) -> list[str]:
    if name.endswith(SKIP_SUFFIX) or Path(name).name in SKIP_NAMES:
        return []
    hits = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line) or ALLOW.search(line):
            continue
        for label, pat in PATTERNS:
            if pat.search(line):
                hits.append(f"{name}:{line_no}  {label}")
                break
    return hits


def staged_files() -> list[str]:
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=child_env())
    return [f for f in r.stdout.split("\n") if f.strip()]


def read_staged(path: str) -> str:
    r = subprocess.run(["git", "show", f":{path}"], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=child_env())
    return r.stdout


def scan_history() -> list[str]:
    """掃所有 blob 的內容（搬家到 GitHub 之前跑，確認歷史裡沒有金鑰）。"""
    hits = []
    r = subprocess.run(["git", "rev-list", "--objects", "--all"], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=child_env())
    for line in r.stdout.splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        obj, name = parts
        t = subprocess.run(["git", "cat-file", "-t", obj], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=child_env()).stdout.strip()
        if t != "blob":
            continue
        content = subprocess.run(["git", "cat-file", "-p", obj], cwd=ROOT,
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", env=child_env()).stdout
        hits += [f"（歷史 {obj[:8]}）{h}" for h in scan_text(name, content)]
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="掃整個工作區")
    ap.add_argument("--history", action="store_true", help="掃所有 commit 的歷史")
    a = ap.parse_args()

    in_git = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                            capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=child_env()).returncode == 0
    if (a.history or not a.all) and not in_git:
        print("check_secrets：這個目錄還不是 git 版本庫，改掃整個工作區")
        a.all, a.history = True, False

    hits: list[str] = []
    if a.history:
        hits = scan_history()
        scope = "全部 commit 歷史"
    elif a.all:
        for f in ROOT.rglob("*"):
            if not f.is_file() or ".git/" in str(f) or f.stat().st_size > 2_000_000:
                continue
            rel = str(f.relative_to(ROOT)).replace("\\", "/")
            if in_git and subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT,
                                         capture_output=True).returncode == 0:
                continue
            # 任一層目錄命中就跳過——原本只看第一層，所以 tests/__pycache__ 的 .pyc
            # 會被掃到，還真的在裡面找到編譯進去的測試假金鑰。
            if any(part in EXCLUDED_DIRS for part in Path(rel).parts[:-1]):
                continue
            if f.suffix in (".pyc", ".pyo", ".so", ".dll", ".zip", ".db", ".png", ".jpg", ".pdf"):
                continue
            hits += scan_text(rel, f.read_text(encoding="utf-8", errors="ignore"))
        scope = "工作區（已排除 .gitignore 的檔案）"
    else:
        for f in staged_files():
            hits += scan_text(f, read_staged(f))
        scope = "已 staged 的變更"

    if hits:
        print(f"🛑 check_secrets：在{scope}裡找到疑似金鑰 {len(hits)} 處")
        for h in hits:
            print("   " + h)
        print("\n   私有庫在 GitHub Free 方案沒有 push protection，這是最後一道防線。")
        print("   → 把值搬進 router/.env（已在 .gitignore），程式改讀環境變數。")
        print("   → 若確定是誤判：加上 placeholder 字樣，或把檔名改成 *.example。")
        print("   → 若已經推出去：先去交易所 / Discord 撤銷重發，再處理歷史。")
        return 1

    print(f"check_secrets：{scope} 沒有發現金鑰")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
