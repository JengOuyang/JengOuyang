#!/usr/bin/env python3
"""scan_legacy.py — 盤點一個或多個既有專案裡可複用的資產，產出 CEO 可讀的清單。

為什麼要有這支程式：
    你在別的 Claude Code 專案已經做出可用的 K 線採集、策略、戰情室、Bitget 串接等等，
    而且不只一個專案。直接把整包丟給 15 個 Agent 讀會造成兩個問題：
      1. 認知污染——舊專案的規則、命名、假設會混進新 Agent 的 context
      2. token 爆量——沒有人需要讀完整個 repo
    所以流程是：**程式盤點 → 產生清單與比較表 → 你決定 → CEO 逐檔派工 → FORGE 只讀被指派的檔**。

多專案的重點是「同一種能力有多個候選」：
    三個專案都有 K 線採集時，CEO 必須看到三個候選、它們的行數與依賴、
    以及你在 legacy/projects.yaml 標的 trust 與 proven，才能選對那一個。

用法：
    python scripts/scan_legacy.py --all                       # 依 legacy/projects.yaml 盤點全部
    python scripts/scan_legacy.py --project qt                # 只盤點一個
    python scripts/scan_legacy.py --src C:/old --id adhoc     # 臨時盤點沒登錄的專案
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy"

# 舊專案的檔案 → 本專案的能力（關鍵字比對，寧可多列也不要漏）
CAPABILITY_HINTS = {
    "market-data-collection": ["ohlcv", "kline", "candle", "collect", "fetch_klines", "ccxt", "binance", "bitget"],
    "exchange-order-placement": ["place_order", "create_order", "submit_order", "usdt-futures", "producttype"],
    "exchange-position-guard": ["position", "stop_loss", "take_profit", "leverage", "margin"],
    "exchange-reconciliation": ["reconcile", "fills", "balance", "equity"],
    "smc-analysis": ["order_block", "fvg", "liquidity", "choch", "bos", "swing"],
    "pattern-analysis": ["head_shoulder", "double_top", "triangle", "wedge", "flag", "pattern"],
    "ratchet-management": ["trail", "ratchet", "breakeven", "move_stop"],
    "backtest-walkforward": ["backtest", "walk_forward", "sharpe", "max_drawdown", "equity_curve"],
    "war-room-dashboard": ["fastapi", "flask", "dashboard", "websocket", "uvicorn", "chart.js", "echarts"],
    "macro-briefing": ["macro", "fred", "cpi", "fomc", "news", "rss"],
    "canva-content": ["canva", "render_image", "pillow", "matplotlib", "post_image"],
    "notion-push": ["notion", "notion_client", "database_id"],
    "remote-access": ["tailscale", "ngrok", "cloudflared", "reverse_proxy"],
    "data-integrity": ["sqlite", "parquet", "hash", "sha256", "merkle", "append_only"],
    "discord-protocol": ["discord", "webhook", "bot.run", "gateway"],
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".pytest_cache", ".next"}
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sql", ".yaml", ".yml", ".json", ".md", ".ps1", ".sh", ".html"}
MAX_BYTES = 2_000_000


def imports_of(path: Path, text: str) -> list[str]:
    if path.suffix != ".py":
        return sorted(set(re.findall(r"(?:require|from)\s*\(?['\"]([\w@/\-.]+)", text)))[:12]
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    return sorted(mods)[:12]


def scan(src: Path, pid: str) -> list[dict]:
    out = []
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in CODE_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.stat().st_size > MAX_BYTES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        low = text.lower()
        caps = [c for c, keys in CAPABILITY_HINTS.items() if sum(k in low for k in keys) >= 2]
        if not caps and p.suffix in {".md", ".json"}:
            continue
        out.append({
            "project": pid,
            "path": str(p.relative_to(src)).replace("\\", "/"),
            "lines": text.count("\n") + 1,
            "imports": imports_of(p, text),
            "capabilities": caps,
            "has_secrets": bool(re.search(r"(api[_-]?key|secret|passphrase|token)\s*[:=]\s*['\"][^'\"]{8,}", text, re.I)),
        })
    return out


def render_project(rows: list[dict], meta: dict) -> str:
    by_cap: dict[str, list[dict]] = {}
    for r in rows:
        for c in r["capabilities"] or ["_未分類"]:
            by_cap.setdefault(c, []).append(r)
    L = [f"# 舊專案盤點：{meta.get('name', meta['id'])}（`{meta['id']}`）", "",
         "> 由 `python scripts/scan_legacy.py` 自動生成，**不要手改表格**——只有「決定」欄是給你填的。", "",
         f"- 路徑：`{meta['path']}`", f"- 狀態：{meta.get('status','?')}　信任度：{meta.get('trust','?')}",
         f"- 檔案數：{len(rows)}", ""]
    if meta.get("proven"):
        L += ["## 已驗證的事實（CEO 派工時的優先依據）", ""] + [f"- {x}" for x in meta["proven"]] + [""]
    if meta.get("known_issues"):
        L += ["## 踩過的坑（比程式本身更值錢——移植時必須保留這些處理）", ""] + [f"- {x}" for x in meta["known_issues"]] + [""]
    sec = [r for r in rows if r["has_secrets"]]
    if sec:
        L += ["## ⚠️ 含疑似金鑰的檔案（移植前必須先清掉，並在交易所端輪換）", ""] + [f"- `{r['path']}`" for r in sec] + [""]
    L += ["## 依能力分類", ""]
    for cap in sorted(by_cap):
        L += [f"### {cap}", "", "| 檔案 | 行數 | 主要依賴 | 決定 |", "|---|---|---|---|"]
        for r in sorted(by_cap[cap], key=lambda x: -x["lines"])[:15]:
            L.append(f"| `{r['path']}` | {r['lines']} | {', '.join(r['imports'][:5]) or '—'} | |")
        L.append("")
    return "\n".join(L)


def render_index(all_rows: list[dict], metas: list[dict]) -> str:
    caps: dict[str, dict[str, list[dict]]] = {}
    for r in all_rows:
        for c in r["capabilities"]:
            caps.setdefault(c, {}).setdefault(r["project"], []).append(r)
    trust = {m["id"]: m.get("trust", "?") for m in metas}
    order = {"high": 0, "medium": 1, "low": 2, "?": 3}

    L = ["# 11 — 既有專案可複用資產（索引）", "",
         "> 由 `python scripts/scan_legacy.py --all` 生成。每個專案的細表在 `docs/legacy/<id>.md`。", "",
         "## 專案", "", "| 代號 | 名稱 | 狀態 | 信任度 | 檔案數 | 細表 |", "|---|---|---|---|---|---|"]
    for m in metas:
        n = len([r for r in all_rows if r["project"] == m["id"]])
        L.append(f"| `{m['id']}` | {m.get('name','')} | {m.get('status','')} | {m.get('trust','')} | {n} | [細表](legacy/{m['id']}.md) |")

    L += ["", "## 能力對照（同一種能力有多個候選時，CEO 只能選一個來源）", "",
          "**選擇規則**：先看信任度（production/high 優先），同級再看「已驗證的事實」是否涵蓋這個能力，"
          "最後才看行數。**不要合併兩個專案的同一種能力**——那會同時繼承兩邊的假設。", "",
          "| 能力 | 候選（專案：檔數／最大檔行數） | 建議來源 | 你的決定 |", "|---|---|---|---|"]
    for cap in sorted(caps):
        cands, best = [], None
        for pid, rows in sorted(caps[cap].items(), key=lambda kv: order.get(trust.get(kv[0], "?"), 3)):
            cands.append(f"`{pid}`：{len(rows)} 檔／{max(r['lines'] for r in rows)} 行（{trust.get(pid,'?')}）")
            best = best or pid
        L.append(f"| {cap} | {'；'.join(cands)} | `{best}` | |")

    L += ["", "## 給 CEO 的派工規則", "",
          "1. 只派 **決定欄為 PORT** 的項目；`REF` 只允許讀來當參考，不得複製進 repo。",
          "2. 一次一個能力，`legacy_paths[]` 逐檔列出——FORGE 只能讀被指派的檔。",
          "3. 指定 `legacy-port` skill；驗收必須附 `verify_delivery.py` 的輸出。",
          "4. 同一能力有多個候選時，在 `TASK_ASSIGN` 註明「為什麼選這個來源、放棄哪些」，寫進建置日報。",
          "5. **移植「坑」比移植程式重要**：每個專案的「踩過的坑」必須變成新程式裡的測試案例，"
          "否則你會用新程式再踩一次。", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="盤點 legacy/projects.yaml 裡的全部專案")
    ap.add_argument("--project", help="只盤點這個代號")
    ap.add_argument("--src", help="臨時盤點一個沒登錄的路徑")
    ap.add_argument("--id", default="adhoc", help="搭配 --src 使用的代號")
    a = ap.parse_args()

    metas: list[dict] = []
    if a.src:
        metas = [{"id": a.id, "name": a.id, "path": a.src, "status": "?", "trust": "?"}]
    else:
        reg = LEGACY / "projects.yaml"
        if not reg.exists():
            print(f"找不到 {reg}。先複製範本：Copy-Item legacy\\projects.yaml.example legacy\\projects.yaml")
            return 1
        metas = yaml.safe_load(reg.read_text(encoding="utf-8"))["projects"]
        if a.project:
            metas = [m for m in metas if m["id"] == a.project] or []
            if not metas:
                print(f"projects.yaml 裡沒有代號 {a.project}")
                return 1

    (ROOT / "docs" / "legacy").mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    for m in metas:
        src = Path(str(m["path"])).expanduser()
        if not src.is_dir():
            print(f"  跳過 {m['id']}：找不到 {src}")
            continue
        rows = scan(src, m["id"])
        all_rows += rows
        (ROOT / "docs" / "legacy" / f"{m['id']}.md").write_text(render_project(rows, m), encoding="utf-8")
        n = sum(r["has_secrets"] for r in rows)
        print(f"  {m['id']}: {len(rows)} 檔、{len({c for r in rows for c in r['capabilities']})} 種能力"
              + (f"、⚠️ {n} 檔疑似含金鑰" if n else ""))

    if not all_rows:
        print("沒有掃到任何檔案——確認路徑是否正確")
        return 1

    (ROOT / "docs" / "11_LEGACY_ASSETS.md").write_text(render_index(all_rows, metas), encoding="utf-8")
    LEGACY.mkdir(exist_ok=True)
    (LEGACY / "inventory.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成：{len(metas)} 個專案、{len(all_rows)} 個檔案 → docs/11_LEGACY_ASSETS.md（索引）+ docs/legacy/<id>.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
