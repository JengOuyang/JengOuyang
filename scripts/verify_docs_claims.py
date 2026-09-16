#!/usr/bin/env python3
"""verify_docs_claims.py — 驗證文件裡宣稱的數字與路徑，與 repo 的實際狀況一致。

存在的理由：白皮書說「41 個視圖」、實際 44 個；說「8 項 lint 檢查」、實際 14 項。
這種漂移沒有人會發現，直到有人照著文件去驗收。所以改成程式檢查。

用法：
    python scripts/verify_docs_claims.py            # 檢查，不一致回傳 1
    python scripts/verify_docs_claims.py --fix      # 自動改寫可安全改寫的數字
    python scripts/verify_docs_claims.py --list     # 只印出目前的真實數字
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]

# 建置待辦：文件把它們寫成「⬜ 待實作」是正常的，不算缺檔
PLANNED_PREFIXES = ("engine/", "backtest/", "dashboard/", "data/", "logs/", "outbox/", "legacy/")
# 第三方套件名稱不是本 repo 的檔案
THIRD_PARTY = {"discord.py", "index.html", "app.py"}


def planned_files() -> set[str]:
    """從建置待辦（08_BUILD_PLAN 與各 README 的 ⬜ 行）取出「已文件化為待實作」的檔名。"""
    out: set[str] = set()
    srcs = [ROOT / "docs" / "08_BUILD_PLAN.md"] + list(ROOT.rglob("README.md"))
    for f in srcs:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if "⬜" in line or "- [ ]" in line or "待實作" in line:
                out.update(re.findall(r"`?([a-zA-Z0-9_/\\-]+\.(?:py|sql|html|ps1))`?", line))
    # 執行時由工具生成、不該進版控的檔（venv 的啟用腳本、使用者自填的清單）
    RUNTIME = {"Activate.ps1", "activate.ps1", "projects.yaml", "tradedesk.db"}
    return ({p.replace("\\", "/") for p in out} | {Path(p).name for p in out} | RUNTIME)


def facts() -> dict:
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    lint = (ROOT / "scripts" / "lint_agents.py").read_text(encoding="utf-8")
    grants = yaml.safe_load((ROOT / "shared" / "view_grants.yaml").read_text(encoding="utf-8"))
    agents = [d.name for d in (ROOT / "agents").iterdir() if d.is_dir() and not d.name.startswith(".")]
    schema = (ROOT / "db" / "001_schema.sql").read_text(encoding="utf-8")
    views = (ROOT / "db" / "002_views.sql").read_text(encoding="utf-8")
    const = (ROOT / "shared" / "CONSTITUTION.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs" / "03_DISCORD_SETUP.md").read_text(encoding="utf-8")
    return {
        "agents": len(agents),
        "bots": len(cfg["agents"]),                                   # 15 Agent + TD-ROUTER
        "skills": len([d for d in (ROOT / "skills").iterdir() if d.is_dir()]),
        "tables": len(re.findall(r"CREATE TABLE IF NOT EXISTS", schema)),
        "views": len(re.findall(r"CREATE VIEW IF NOT EXISTS", views)),
        "jobs": len(sched["jobs"]),
        # 只認「問題訊息開頭的 [N]」，否則 names[0] 這種陣列索引會被算成一項檢查
        "lint_checks": len({int(n) for n in re.findall(r'f?"\[(\d+)\]', lint)}),
        # 測試數也會漂（13_GITHUB 曾停在 69 而實際 80）
        # 用 pytest 自己數（有 parametrize，數 def test_ 會少算）
        "tests": int(re.search(r"(\d+) tests? collected", subprocess.run(
            # 一定要限定 tests/：不限定的話 pytest 會從專案根目錄往下收，
            # 把 legacy/ 裡的舊專案、或任何使用者自己放的測試也算進去，
            # 於是同一份程式在不同機器上數出不同的數字（實測：這裡 130、Blacksheep 那台 140）。
            [sys.executable, "-m", "pytest", "-q", "--collect-only", "tests"], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=child_env()).stdout or "0 tests collected").group(1)),
        "channels": len(re.findall(r"^\| [^|]*\| #", setup, re.M)) or len(set(re.findall(r"CH_[A-Z_]+", setup))),
        "adrs": len([f for f in (ROOT / "docs" / "adr").iterdir() if f.name.startswith("ADR")]),
        "iron_rules": len(re.findall(r"^\d+\. \*\*", const, re.M)),
        "granted_views": len(set(grants["common"]) | {v for l in grants["grants"].values() for v in l}),
        "docs": len([f for f in (ROOT / "docs").glob("*.md")]),
        "scripts_impl": len([f for f in (ROOT / "scripts").glob("*.py")]),
    }


# 文件裡的宣稱 → 對應事實。pattern 需有一個數字群組。
CLAIMS = [
    ("db/002_views.sql", r"(\d+)\s*個視圖", "views"),
    ("002_views.sql", r"定義\s*(\d+)\s*個", "views"),
    ("001_schema.sql", r"(\d+)\s*(?:張)?表", "tables"),
    ("lint_agents.py", r"（(\d+)\s*項", "lint_checks"),
    ("pytest", r"（(\d+)\s*項", "tests"),
    ("回歸測試", r"(\d+)\s*項", "tests"),
    ("lint_agents.py", r"(\d+)\s*項自洽檢查", "lint_checks"),
    ("個排程", r"(\d+)\s*個排程", "jobs"),
    ("持有", r"持有\s*(\d+)\s*隻 Bot", "bots"),
    ("全部上線", r"(\d+)\s*隻 Bot 全數上線", "bots"),
    ("個 Agent", r"(\d+)\s*個 AI Agent", "agents"),
    ("鐵律", r"(\d+)\s*條鐵律", "iron_rules"),
]


def check(fix: bool) -> int:
    f = facts()
    bad, fixed = [], 0
    zh = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}

    for md in sorted(list((ROOT / "docs").rglob("*.md")) + list(ROOT.glob("*.md")) +
                     list((ROOT / "shared").glob("*.md")) + list((ROOT / "router").glob("*.md")) +
                     list((ROOT / "db").glob("*.md")) + list((ROOT / "scripts").glob("*.md")) +
                     list((ROOT / "skills").glob("README.md")) + list((ROOT / "engine").glob("*.md")) +
                     list((ROOT / "tests").glob("*.md"))):
        text = md.read_text(encoding="utf-8")
        orig = text
        # CHANGELOG 的工作就是記錄「當初那個數字錯了」，不能拿現在的事實去改它
        numbers_are_history = md.name == "CHANGELOG.md"
        for lineno, line in enumerate(text.splitlines(), 1):
            if numbers_are_history:
                break
            for anchor, pat, key in CLAIMS:
                if anchor not in line:
                    continue
                for m in re.finditer(pat, line):
                    got, want = int(m.group(1)), f[key]
                    if got == want:
                        continue
                    rel = md.relative_to(ROOT)
                    if fix:
                        text = text.replace(m.group(0), m.group(0).replace(str(got), str(want), 1))
                        fixed += 1
                    else:
                        bad.append(f"{rel}:{lineno} 宣稱 {key}={got}，實際 {want}｜{line.strip()[:90]}")
        # 中文數字的鐵律條數（「七條鐵律」）
        want_cn = zh.get(f["iron_rules"])
        if want_cn:
            for m in re.finditer(r"([一二三四五六七八九十])條鐵律", text):
                if m.group(1) != want_cn:
                    if fix:
                        text = text.replace(m.group(0), f"{want_cn}條鐵律")
                        fixed += 1
                    else:
                        bad.append(f"{md.relative_to(ROOT)} 宣稱「{m.group(0)}」，實際 {f['iron_rules']} 條")
        if fix and text != orig:
            md.write_text(text, encoding="utf-8")

    # 路徑宣稱：文件裡的 `路徑` 必須存在，或屬於已文件化的建置待辦
    PLANNED = planned_files()
    for md in sorted((ROOT / "docs").glob("*.md")) + sorted((ROOT / "shared").glob("*.md")) + [ROOT / "QUICKSTART.md", ROOT / "README.md"]:
        if not md.exists():
            continue
        # CHANGELOG 會引用「第三方套件的檔案」當證據（例如 pandas/io/clipboard/__init__.py
        # 是 v3.0.6 那個 .venv 誤掃 bug 的現場），那些檔案本來就不在我們的版本庫裡
        if md.name == "CHANGELOG.md":
            continue
        for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for raw in re.findall(r"`([a-zA-Z0-9_./\\-]+\.(?:py|md|yaml|json|sql|ps1|html))`", line):
                rel = raw.replace("\\", "/")
                if rel.startswith(PLANNED_PREFIXES) or "*" in rel or "<" in rel:
                    continue
                if rel in THIRD_PARTY or Path(rel).name in THIRD_PARTY:
                    continue
                if rel in PLANNED or Path(rel).name in PLANNED:
                    continue
                if not (ROOT / rel).exists() and not list(ROOT.rglob(Path(rel).name)):
                    bad.append(f"{md.relative_to(ROOT)}:{lineno} 引用了不存在的檔案：{rel}")

    if fix:
        print(f"verify_docs_claims：已修正 {fixed} 處數字")
        return 0
    print(f"實際數字：{', '.join(f'{k}={v}' for k, v in facts().items())}")
    for b in dict.fromkeys(bad):
        print("  ERROR", b)
    if bad:
        print(f"\n失敗：{len(set(bad))} 處文件與實際不符（可先跑 --fix 修數字）")
        return 1
    print("通過：文件宣稱的數字與路徑都與 repo 一致")
    return 0


if __name__ == "__main__":
    if "--list" in sys.argv:
        for k, v in facts().items():
            print(f"{k:14s} {v}")
        raise SystemExit(0)
    raise SystemExit(check("--fix" in sys.argv))
