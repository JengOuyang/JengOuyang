#!/usr/bin/env python3
"""
verify_delivery.py — 獨立驗收。CEO 用它檢查 FORGE / LAB 的交付，而不是相信對方貼上來的測試輸出。

「你不能讓一個人自己幫自己打分數」——交付者自報的 pytest 結果不算證據，
因為它可能是舊的、是別的檔案的、或根本是編的。這支程式自己跑一次。

用法（CEO）：
    python ../../scripts/verify_delivery.py --task T-2026-0912-003 \
        --tests tests/test_risk_gate.py --files engine/risk_gate.py

輸出 JSON：{verdict: PASS|FAIL, checks: [...]}，CEO 直接引用這份結果做 REVIEW_RESULT。
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout,
                           encoding="utf-8", errors="replace", env=child_env())
        return r.returncode, (r.stdout + r.stderr)[-3000:]
    except subprocess.TimeoutExpired:
        return 124, f"逾時（{timeout}s）"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--tests", nargs="*", default=[], help="必須通過的測試檔")
    ap.add_argument("--files", nargs="*", default=[], help="交付宣稱新增或修改的檔案")
    args = ap.parse_args()

    checks, t0 = [], time.time()

    for f in args.files:
        p = ROOT / f
        checks.append({"check": f"檔案存在 {f}", "pass": p.exists(),
                       "detail": f"{p.stat().st_size} bytes" if p.exists() else "找不到"})

    for t in args.tests:
        if not (ROOT / t).exists():
            checks.append({"check": f"測試 {t}", "pass": False, "detail": "測試檔不存在——交付未附測試"})
            continue
        code, out = run([sys.executable, "-m", "pytest", t, "-q"])
        checks.append({"check": f"測試 {t}", "pass": code == 0, "detail": out[-800:]})

    code, out = run([sys.executable, str(ROOT / "scripts" / "lint_agents.py")])
    checks.append({"check": "lint_agents", "pass": code == 0, "detail": out[-800:]})

    code, out = run([sys.executable, str(ROOT / "scripts" / "build_context.py"), "--verify"])
    checks.append({"check": "上下文完整性", "pass": code == 0, "detail": out[-400:]})

    code, out = run(["git", "status", "--porcelain"])
    checks.append({"check": "工作區有實際變更", "pass": bool(out.strip()),
                   "detail": out[:600] or "沒有任何檔案變更——交付可能是空的"})

    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    print(json.dumps({"task": args.task, "verdict": verdict, "checks": checks,
                      "verified_by": "scripts/verify_delivery.py", "elapsed_s": round(time.time() - t0, 1)},
                     ensure_ascii=False, indent=2))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
