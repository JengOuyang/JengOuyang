#!/usr/bin/env python3
"""verify_isolation.py — 驗證四件事，而且是用程式驗證，不是用文件宣稱。

  1. 責任不重疊：shared/OWNERSHIP.yaml 的每一項責任恰好一個 owner
  2. 交接無縫：每個 handoff 的產出者與接收者都在 PROTOCOL 與雙方手冊裡
  3. 角色不混淆：每個 Agent 的人設有明確界線句，且不描述別人的職責
  4. 權限隔離：settings.json 的 allow/deny 與 OWNERSHIP 的寫入權相符，
     並**主動找出逃逸路徑**（能寫檔 + 能執行任意程式 = 工具層限制形同虛設）

用法：
    python scripts/verify_isolation.py            # 全部檢查
    python scripts/verify_isolation.py --escapes  # 只列逃逸路徑（誠實報告用）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]

# 能執行任意程式的樣式：拿到這個 + 任何寫入權 = 可繞過工具層
ARBITRARY_EXEC = [
    re.compile(r"^Bash\(python \*\)$"),
    re.compile(r"^Bash\(python3? [^)]*\*\)$"),          # Bash(python ../../backtest/*) 也算
    re.compile(r"^Bash\(\*\)$"),
    re.compile(r"^Bash\(sh .*\)$"),
    re.compile(r"^Bash\(pwsh?.*\)$"),
    re.compile(r"^Bash$"),
]
# 明確指定單一腳本的呼叫不算（那支腳本本身就是守門程式）
SINGLE_SCRIPT = re.compile(r"^Bash\((?:python3? )?[\w./-]+\.py[^*]*\*?\)$")

WRITE_TOOL = re.compile(r"^(Write|Edit|NotebookEdit)(\(|$)")


def load():
    return (
        yaml.safe_load((ROOT / "shared" / "OWNERSHIP.yaml").read_text(encoding="utf-8")),
        yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))["agents"],
        {d.name: json.loads((d / ".claude" / "settings.json").read_text(encoding="utf-8"))
         for d in sorted((ROOT / "agents").iterdir()) if (d / ".claude" / "settings.json").exists()},
    )


def check_responsibilities(own, problems):
    """1. 每項責任恰好一個 owner；owner 必須是真的 Agent。"""
    agents = {d.name for d in (ROOT / "agents").iterdir() if d.is_dir()}
    seen: dict[str, str] = {}
    for name, spec in own["responsibilities"].items():
        o = spec["owner"]
        if o not in agents:
            problems.append(f"[責任] {name} 的 owner「{o}」不是現有 Agent")
        seen.setdefault(o, "")
    # 手冊裡不得出現「別人的責任」被當成自己的職責
    for name, spec in own["responsibilities"].items():
        owner = spec["owner"]
        key = name.replace("_", "")
        for other in agents - {owner}:
            m = ROOT / "agents" / other / "MANUAL.md"
            if not m.exists():
                continue
            duties = m.read_text(encoding="utf-8").split("## 觸發方式")[0]
            if key in duties.replace(" ", ""):
                problems.append(f"[重疊] {other} 的職責段提到「{name}」，但 owner 是 {owner}")


def check_handoffs(own, problems):
    """2. 交接的兩端都必須在自己的手冊裡承認這條鏈。"""
    proto = (ROOT / "shared" / "PROTOCOL.md").read_text(encoding="utf-8")
    for h in own["handoffs"]:
        msg = h["msg"]
        if f"| {msg} |" not in proto:
            problems.append(f"[交接] {msg} 不在 PROTOCOL.md 的 msg_type 表")
        src = h["from"]
        if src != "any":
            m = ROOT / "agents" / src / "MANUAL.md"
            if m.exists() and msg not in m.read_text(encoding="utf-8"):
                problems.append(f"[交接] 產出者 {src} 的手冊沒有提到 {msg}")
        for dst in h["to"]:
            m = ROOT / "agents" / dst / "MANUAL.md"
            if m.exists() and msg not in m.read_text(encoding="utf-8"):
                problems.append(f"[交接] 接收者 {dst} 的手冊沒有提到 {msg}（這條鏈會斷在它這裡）")


def check_role_clarity(problems):
    """3. 每個 Agent 都要有「與相近角色的界線」或等效的唯一身分聲明。"""
    CONFUSABLE = {"risk", "redteam", "audit", "lab", "forge", "feed", "ledger", "creative", "cmo", "growth"}
    for a in sorted(CONFUSABLE):
        p = ROOT / "agents" / a / "PERSONA.md"
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        if "與相近角色的界線" not in s and "我不做" not in s:
            problems.append(f"[角色] {a}/PERSONA.md 沒有與相近角色的界線句——容易被混淆")


def check_write_isolation(own, cfg, settings, problems, escapes):
    """4. 寫入權必須與 OWNERSHIP 相符，並找出逃逸路徑。"""
    paths = own["writable_paths"]

    for agent, st in settings.items():
        allow = st["permissions"]["allow"]
        deny = set(st["permissions"]["deny"])

        # 4a 任何人都不得寫的路徑，必須出現在 deny
        for must_deny in ("Write(../../shared/**)", "Edit(../../shared/**)",
                          "Write(.context/**)", "Edit(.context/**)",
                          "Read(../../router/.env)"):
            if must_deny not in deny:
                problems.append(f"[權限] {agent} 的 deny 缺少 {must_deny}")

        # 4b 宣告的寫入路徑必須是它擁有的（先正規化成 repo 相對路徑）
        for a in allow:
            m = re.match(r"^(?:Write|Edit)\((.+)\)$", a)
            if not m:
                continue
            raw = m.group(1)
            target = raw[6:] if raw.startswith("../../") else f"agents/{agent}/{raw}"
            owner = None
            for pat, spec in paths.items():
                pat_norm = pat.replace("<self>", agent).replace("*", "")
                if target.replace("*", "").startswith(pat_norm.rstrip("/")):
                    owner, how = spec["owner"], pat
                    break
                # agents/*/X 這種樣式
                if "*" in pat and re.match(pat.replace("**", ".*").replace("*", "[^/]*"), target):
                    owner, how = spec["owner"], pat
                    break
            if owner is None:
                problems.append(f"[權限] {agent} 可寫 {target}，但 OWNERSHIP.yaml 沒有定義這條路徑的 owner")
            elif owner not in (agent, "any_self"):
                problems.append(f"[權限] {agent} 可寫 {target}（規則 {how}），但該路徑的 owner 是 {owner}")

        # 4c 逃逸路徑：能寫檔 + 能執行任意程式
        can_write = [a for a in allow if WRITE_TOOL.match(a)]
        can_exec = [a for a in allow
                    if any(p.match(a) for p in ARBITRARY_EXEC) and not SINGLE_SCRIPT.match(a)]
        if can_write and can_exec:
            escapes.append((agent, can_write, can_exec))

        # 4d 裸 Write/Edit（無路徑限制）
        for a in allow:
            if a in ("Write", "Edit"):
                problems.append(f"[權限] {agent} 有無路徑限制的 `{a}`——必須收斂成目錄白名單")


def check_os_sandbox(own, settings, problems) -> list[str]:
    """5. L0：每個 Agent 都要有 OS 層沙箱區塊，且 denyWrite 必須涵蓋它不擁有的路徑。

    這一層是 2026 年 Claude Code 才補上的能力（bubblewrap / Seatbelt），
    限制會套用到 Bash 指令**與其所有子程序**——也就是 4c 找出的逃逸路徑真正被關上的地方。
    回傳「沙箱有效涵蓋」的 Agent 清單，供逃逸報告判斷嚴重性。
    """
    covered = []
    for agent, st in sorted(settings.items()):
        sb = st.get("sandbox")
        if not sb or not sb.get("enabled"):
            problems.append(f"[L0] {agent} 沒有啟用 OS 層沙箱（跑 `python scripts/sync_sandbox.py`）")
            continue
        fs = sb.get("filesystem", {})
        dw = set(fs.get("denyWrite", []))
        owned_tops = {p.replace("<self>", agent).split("/")[0]
                      for p, s in own["writable_paths"].items() if s["owner"] in (agent, "any_self")}
        missing = [f"../../{d}" for d in ("shared", "engine", "router", "scripts", "db", "docs", "tests", "data")
                   if d not in owned_tops and f"../../{d}" not in dw]
        if missing:
            problems.append(f"[L0] {agent} 的沙箱 denyWrite 缺少：{', '.join(missing)}")
            continue
        if "../../router/.env" not in set(fs.get("denyRead", [])):
            problems.append(f"[L0] {agent} 的沙箱沒有擋掉 router/.env 的讀取")
            continue
        covered.append(agent)
    return covered


def main() -> int:
    own, cfg, settings = load()
    problems: list[str] = []
    escapes: list[tuple] = []

    check_responsibilities(own, problems)
    check_handoffs(own, problems)
    check_role_clarity(problems)
    check_write_isolation(own, cfg, settings, problems, escapes)
    covered = check_os_sandbox(own, settings, problems)

    only_escapes = "--escapes" in sys.argv
    if not only_escapes:
        print(f"隔離驗證：{len(own['responsibilities'])} 項責任、{len(own['handoffs'])} 條交接、"
              f"{len(settings)} 個 Agent 的權限")
        for p in problems:
            print("  ERROR", p)

    if escapes:
        # L0 是否**真的**生效，取決於執行平台與 TD_REQUIRE_SANDBOX，不是設定檔寫了就算
        import os, platform
        require = os.environ.get("TD_REQUIRE_SANDBOX", "0") == "1"
        win = platform.system() == "Windows"
        live = require and not win

        print("\n⚠️ 工具層逃逸路徑（能寫檔 + 能執行任意程式 → 單靠 allow/deny 形同建議）：")
        for agent, w, e in escapes:
            if agent not in covered:
                tag = "**連 L0 規則都沒有——跑 sync_sandbox.py**"
            elif live:
                tag = "已由 L0 OS 沙箱封住"
            else:
                tag = "L0 規則已備妥但**目前未生效** → 靠 L3 偵測 + 自動還原"
            print(f"  - {agent}：寫入 {w}　執行 {e}　→ {tag}")

        if live:
            print("  → L0 生效中（TD_REQUIRE_SANDBOX=1，非 Windows）。")
        elif win:
            print("  → 目前是**原生 Windows**：Claude Code 沒有 OS 層沙箱，L0 不存在。")
            print("     隔離 = L1 工具層 + L2 worktree + L3 偵測還原。這是可接受的取捨，")
            print("     但它是「抓得到並自動還原」，不是「擋得住」。")
        else:
            print("  → TD_REQUIRE_SANDBOX=0：L0 規則已生成但未要求。")
            print("     在 macOS / Linux / WSL2 上設為 1 即可啟用。")
        print("     完整取捨與真實成本見 docs/12_DIGITAL_BOUNDARY.md 第四節。")

    if problems:
        print(f"\n失敗：{len(problems)} 個隔離問題")
        return 1
    if not only_escapes:
        print(f"\n通過：責任不重疊、交接兩端齊備、角色界線明確、寫入權與 OWNERSHIP 相符、"
              f"{len(covered)}/{len(settings)} 個 Agent 備妥 L0 沙箱規則")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
