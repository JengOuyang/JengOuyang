#!/usr/bin/env python3
"""
stub_precheck.py — 佔位程式期間，讓每 5 分鐘的 RISK/EXEC 排程安靜下來。

為什麼需要：
    `engine/executor.py` 與 `engine/risk_gate.py` 目前是 NOT_IMPLEMENTED stub，什麼都不做。
    但 risk-account-check / exec-ratchet / exec-reconcile 每 5 分鐘各觸發一次，
    每次都在 Discord 發訊息、開 thread、貼「（無輸出）」——一天約 860 個空 thread。

安全原則（任何疑慮都「照常執行」，絕不因誤判而跳過真正的熔斷／棘輪／對帳）：
    1. `strategy_params.yaml` 的 mode 不是 DEMO → 一律 RUN
    2. 目標檔的 docstring 第一行不是「<檔名> — NOT_IMPLEMENTED stub」→ RUN
    3. 目標檔超過 STUB_MAX_LINES 行（像是真的實作了、只是忘了改檔頭）→ RUN
    4. 目標檔有模組層級的 IMPLEMENTED 且含這個子命令 → RUN
    5. 讀檔、解析、任何例外 → RUN
    真正的實作上線（換掉檔頭）後自動放行，不需要回來關掉。

用法（Router 的 precheck 約定：輸出以 SKIP 開頭則不觸發）：
    python scripts/stub_precheck.py engine/executor.py ratchet
    python scripts/stub_precheck.py engine/risk_gate.py --account-check
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
STUB_MAX_LINES = 80


def decide(target: Path, subcommand: str, params_path: Path) -> tuple[str, str]:
    """回傳 ("SKIP" | "RUN", 理由)。"""
    try:
        mode = (yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}).get("mode")
        if mode != "DEMO":
            return "RUN", f"mode={mode}（非 DEMO 一律執行）"
        text = target.read_text(encoding="utf-8")
        if text.count("\n") + 1 > STUB_MAX_LINES:
            return "RUN", f"{target.name} 超過 {STUB_MAX_LINES} 行，不視為佔位程式"
        tree = ast.parse(text)
        doc = (ast.get_docstring(tree) or "").strip().splitlines()
        if not doc or doc[0].strip() != f"{target.name} — NOT_IMPLEMENTED stub":
            return "RUN", f"{target.name} 沒有佔位程式標記"
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "IMPLEMENTED" for t in node.targets)):
                value = node.value
                if isinstance(value, ast.Call):          # set() / set([...])
                    items = value.args[0] if value.args else ast.List(elts=[])
                else:
                    items = value
                done = {e.value for e in getattr(items, "elts", []) if isinstance(e, ast.Constant)}
                if subcommand in done:
                    return "RUN", f"{target.name} {subcommand} 已實作"
        return "SKIP", f"{target.name} {subcommand} 仍是 NOT_IMPLEMENTED stub（DEMO）"
    except Exception as e:                               # 判斷不了就照常執行
        return "RUN", f"無法判斷（{type(e).__name__}），照常執行"


def main() -> int:
    if len(sys.argv) != 3:
        print("RUN 參數錯誤，照常執行（用法：stub_precheck.py <檔案> <子命令>）")
        return 0
    verdict, why = decide(ROOT / sys.argv[1], sys.argv[2], ROOT / "shared" / "strategy_params.yaml")
    print(f"{verdict} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
