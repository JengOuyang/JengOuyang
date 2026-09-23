#!/usr/bin/env python3
"""guard_paths.py — 受保護檔案的完整性守衛（L3 偵測層）。

為什麼需要它：
    Claude Code 的 allow/deny 是**工具層**授權，不是 OS 沙箱。
    FORGE 與 LAB 同時擁有「寫檔」與「執行任意程式」（它們的工作需要），
    理論上可以寫一支腳本再執行它來繞過 allow/deny。
    verify_isolation.py 會誠實列出這些逃逸路徑——而這支程式負責在它們真的發生時抓到。

做法（快照 → 執行 → 比對 → 還原）：
    Router 在每次呼叫 Agent 前 snapshot，呼叫後 verify；
    發現受保護檔案被改動且該 Agent 無權改 → 自動 git 還原、寫 #alerts、把 system_state 設為 HALT。

用法：
    python scripts/guard_paths.py snapshot                 # 建立基準（Router preflight）
    python scripts/guard_paths.py verify --agent forge     # 比對；有未授權變更回傳 1
    python scripts/guard_paths.py verify --agent forge --restore   # 比對並自動還原
    python scripts/guard_paths.py status
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "router" / "guard_state.json"

# 受保護：這些路徑的任何變更都必須有授權來源（merge_fix.py 或 apply_change.py）
PROTECTED = [
    "shared/**/*.md", "shared/*.yaml", "shared/schemas/*.json",
    "router/*.py", "router/*.yaml", "router/*.ps1",
    "scripts/*.py", "engine/*.py", "db/*.sql",
    "agents/*/PERSONA.md", "agents/*/MANUAL.md", "agents/*/USER.md",
    "agents/*/CLAUDE.md", "agents/*/.claude/settings.json",
    "agents/*/.context/*.md", "agents/*/.context/MANIFEST.json",
    "tests/*.py", ".gitignore",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect() -> dict[str, str]:
    out = {}
    for pat in PROTECTED:
        for p in sorted(ROOT.glob(pat)):
            if p.is_file():
                out[str(p.relative_to(ROOT)).replace("\\", "/")] = sha(p)
    return out


def snapshot() -> int:
    files = collect()
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    git_head = r.stdout.strip() if r.returncode == 0 else ""
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"git_head": git_head, "files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"guard_paths：已建立基準，{len(files)} 個受保護檔案")
    return 0


def allowed_for(agent: str) -> list[str]:
    """該 Agent 依 OWNERSHIP.yaml 有權改動的 repo 相對路徑前綴。"""
    own = yaml.safe_load((ROOT / "shared" / "OWNERSHIP.yaml").read_text(encoding="utf-8"))
    out = [f"agents/{agent}/outbox/"]
    for pat, spec in own["writable_paths"].items():
        if spec["owner"] in (agent, "any_self"):
            out.append(pat.replace("<self>", agent).split("*")[0])
    return out


def verify(agent: str | None, restore: bool) -> int:
    if not STATE.exists():
        print("guard_paths：沒有基準，先跑 snapshot"); return 2
    state_data = json.loads(STATE.read_text(encoding="utf-8"))
    base = state_data["files"]
    # 向下相容：舊格式沒有 git_head，fallback 到 "--"（還原工作目錄到 HEAD）
    baseline_ref = state_data.get("git_head") or "--"
    now = collect()
    ok_prefixes = allowed_for(agent) if agent else []

    changed = [f for f in set(base) | set(now) if base.get(f) != now.get(f)]
    unauthorized = [f for f in changed if not any(f.startswith(p) for p in ok_prefixes)]

    if not changed:
        print("guard_paths：受保護檔案無變更")
        return 0

    print(f"guard_paths：{len(changed)} 個受保護檔案有變更"
          + (f"（呼叫者：{agent}）" if agent else ""))
    for f in sorted(changed):
        tag = "未授權" if f in unauthorized else "在授權範圍內"
        print(f"  [{tag}] {f}")

    if not unauthorized:
        snapshot()                      # 授權範圍內的變更 → 更新基準
        return 0

    print(f"\n⚠️ {len(unauthorized)} 個未授權變更"
          + ("（依 OWNERSHIP.yaml，這個 Agent 無權改它們）" if agent else ""))
    if restore:
        # 使用基準 commit 的 ref 還原；若 baseline_ref="--" 退回舊行為（還原到 HEAD）
        ref_cmd = [baseline_ref] if baseline_ref != "--" else ["--"]
        all_ok = True
        for f in sorted(unauthorized):
            r = subprocess.run(["git", "checkout"] + ref_cmd + [f], cwd=ROOT,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=child_env())
            # 以 hash 驗證還原是否真的生效，而非只看 returncode
            restored_ok = r.returncode == 0 and (ROOT / f).is_file() and sha(ROOT / f) == base.get(f)
            print(("  已還原 " if restored_ok else "  還原失敗 ") + f
                  + ("" if restored_ok else f"（baseline={baseline_ref[:12]}）：{r.stderr.strip()[:80]}"))
            if not restored_ok:
                all_ok = False
        if all_ok:
            snapshot()                  # 全部還原成功 → 更新基準，中斷連鎖誤報
        print("  → 請同時把 system_state.trading 設為 HALT 並在 #alerts @Blacksheep")
    else:
        print("  → 加 --restore 可自動 git 還原")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["snapshot", "verify", "status"])
    ap.add_argument("--agent", help="剛執行的 Agent id（用來判斷變更是否在它的授權範圍）")
    ap.add_argument("--restore", action="store_true", help="未授權變更自動 git 還原")
    a = ap.parse_args()

    if a.action == "snapshot":
        return snapshot()
    if a.action == "verify":
        return verify(a.agent, a.restore)
    if STATE.exists():
        base = json.loads(STATE.read_text(encoding="utf-8"))["files"]
        print(f"guard_paths：基準涵蓋 {len(base)} 個檔案；目前 {len(collect())} 個")
    else:
        print("guard_paths：尚未建立基準")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
