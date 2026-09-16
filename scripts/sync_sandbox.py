#!/usr/bin/env python3
"""sync_sandbox.py — 由 OWNERSHIP.yaml 生成每個 Agent 的 OS 層沙箱設定（L0）。

為什麼需要它：
    settings.json 的 permissions.allow/deny 是**工具層**授權：Claude Code 在呼叫
    Read/Write/Bash 之前比對規則。它擋不住「已經在跑的子程序」——一個同時擁有
    寫檔與執行程式的 Agent（FORGE、LAB）可以寫一支 .py 再執行它來繞過。
    這就是 verify_isolation.py 一直誠實列出的逃逸路徑。

    Claude Code 內建的 sandbox 是**作業系統層**（Linux/WSL2 用 bubblewrap、
    macOS 用 Seatbelt），限制會套用到 Bash 指令**與它所有子程序**。
    把 OWNERSHIP.yaml 的寫入權翻譯成 sandbox.filesystem 規則，逃逸路徑才真的關上。

    ⚠️ 原生 Windows 不支援 sandbox（Claude Code 官方文件明列）。
       Router 與 15 個 Agent 必須跑在 WSL2 裡，L0 才會生效。
       跑在原生 Windows 時 sandbox 靜默失效 → 由 Router 以 --settings 帶入
       failIfUnavailable=true 讓它「啟動即失敗」，而不是假裝有保護。

用法：
    python scripts/sync_sandbox.py            # 寫入 15 份 settings.json
    python scripts/sync_sandbox.py --verify   # 只檢查，不一致回傳 1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]

# 版本庫最上層目錄；沒有被 OWNERSHIP 指名擁有者的，一律 denyWrite
TOP_DIRS = ["agents", "backtest", "dashboard", "data", "db", "dev", "docs", "engine",
            "legacy", "logs", "marketing", "router", "scripts", "shared", "skills", "tests"]

# 自己目錄裡也不能寫的東西（身分檔與生成物：改了就等於自己改自己的角色）
SELF_PROTECTED = [".context", "MANUAL.md", "PERSONA.md", "USER.md", "CLAUDE.md"]

# 任何 Agent 的子程序都不該讀到的憑證
CRED_FILES = ["~/.ssh", "~/.aws/credentials", "~/.config/gcloud", "~/.docker/config.json"]
CRED_ENVS = ["BITGET_API_KEY", "BITGET_API_SECRET", "BITGET_PASSPHRASE",
             "DISCORD_TOKEN", "NOTION_TOKEN", "GITHUB_TOKEN", "ANTHROPIC_API_KEY"]


def owned_paths(own: dict, agent: str) -> list[str]:
    """該 Agent 依 OWNERSHIP.yaml 可寫的版本庫相對路徑（已去掉萬用字元）。"""
    out = []
    for pat, spec in own["writable_paths"].items():
        if spec["owner"] in (agent, "any_self"):
            out.append(pat.replace("<self>", agent).split("**")[0].rstrip("/"))
    return sorted(set(out))


def expand_star(path: str, agents: list[str]) -> list[str]:
    """把 agents/*/X 這種萬用字元展開成具名路徑（沙箱的路徑比對不保證支援中段 *）。"""
    if "*" not in path:
        return [path]
    if "/agents/*/" in path or path.startswith("agents/*/"):
        return [path.replace("/*/", f"/{a}/", 1) if "/agents/*/" in path
                else path.replace("agents/*/", f"agents/{a}/", 1) for a in agents]
    return [path.split("*")[0].rstrip("/")]


def tool_deny_reads_of(st: dict) -> list[str]:
    """該 Agent 工具層 deny 的 Read 目標（含 Bash(cat X) 這種等效寫法）。"""
    out = []
    for d in st.get("permissions", {}).get("deny", []):
        m = re.match(r"^Read\((.+)\)$", d) or re.match(r"^Bash\(cat ([^ )]+)\)$", d)
        if m:
            out.append(m.group(1).replace("/**", "").rstrip("/"))
    return out


def sandbox_for(own: dict, agent: str, agents: list[str], tool_deny_reads: list[str]) -> dict:
    """agents/<id>/.claude/settings.json 用的 sandbox 區塊。

    路徑慣例：專案設定檔裡沒有前綴的相對路徑以「專案根目錄」為基準，
    這裡的專案根目錄 = agents/<id>/，所以版本庫的 shared/ 寫成 ../../shared。
    """
    owned = owned_paths(own, agent)
    allow_write, deny_write = [], []

    for p in owned:
        if p.startswith(f"agents/{agent}/"):
            allow_write.append("./" + p[len(f"agents/{agent}/"):])   # cwd 內，預設就能寫，寫明是為了可讀
        else:
            allow_write.append("../../" + p)

    owned_tops = {p.split("/")[0] for p in owned}
    for d in TOP_DIRS:
        if d == "agents" or d in owned_tops:
            continue
        deny_write.append(f"../../{d}")

    # agents/ 之下：別人的目錄整個擋掉，自己的目錄只擋身分檔
    for other in agents:
        if other != agent:
            deny_write.append(f"../../agents/{other}")
    deny_write += [f"./{f}" for f in SELF_PROTECTED]
    # 自己擁有 worktree 之類的子路徑時，仍不得寫自己目錄的身分檔（上面那行已涵蓋）

    deny_read = ["../../router/.env"]
    # 其他 Agent 的 USER.md（Owner 的私人指示）任何人都不得讀
    deny_read += [f"../../agents/{o}/USER.md" for o in agents if o != agent]
    # L0 必須鏡射 L1：工具層擋掉的每一條 Read，OS 層也要擋
    # （否則 CHART 被 deny Read(RISK_RULES.md) 卻能用 Bash `cat` 讀到 → Goodhart 防線是紙做的）
    for r in tool_deny_reads:
        deny_read += expand_star(r, agents)
    # 例外一：data/ 不能進 denyRead。工具層擋 Read(../../data/**) 是為了不讓 LLM 直接看原始檔，
    #          但被授權的查詢路徑 scripts/query_readonly.py 是 Bash 子程序，它必須開得了 data/*.db。
    #          （寫入仍然全面禁止——denyWrite 有 ../../data。）
    # 例外二：自己的身分檔不能擋自己。工具層的 Read(../../agents/*/PERSONA.md) 從自己目錄看是
    #          相對路徑，擋不到自己；沙箱比對的是真實路徑，不排除就會把自己鎖在門外。
    deny_read = [r for r in deny_read
                 if r and not r.startswith("../../data")
                 and not r.startswith(f"../../agents/{agent}")]

    return {
        "enabled": True,
        "filesystem": {
            "allowWrite": sorted(set(allow_write)),
            "denyWrite": sorted(set(deny_write)),
            "denyRead": sorted(set(deny_read)),
        },
        "network": {
            # LLM Agent 的 Bash 只跑本機查詢腳本，不需要任何外網。
            # 採集與下單是 program 型 Agent（engine/），不經過這裡。
            "allowedDomains": []
        },
        "credentials": {
            "files": [{"path": p, "mode": "deny"} for p in CRED_FILES]
                     + [{"path": "../../router/.env", "mode": "deny"}],
            "envVars": [{"name": n, "mode": "deny"} for n in CRED_ENVS],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    own = yaml.safe_load((ROOT / "shared" / "OWNERSHIP.yaml").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    agents = sorted(k for k, v in cfg["agents"].items() if v.get("kind") != "router")

    bad = 0
    for aid in agents:
        f = ROOT / "agents" / aid / ".claude" / "settings.json"
        if not f.exists():
            print(f"  ERROR {aid}：settings.json 不存在"); bad += 1; continue
        st = json.loads(f.read_text(encoding="utf-8"))
        want = sandbox_for(own, aid, agents, tool_deny_reads_of(st))
        if a.verify:
            if st.get("sandbox") != want:
                print(f"  ERROR {aid}/.claude/settings.json 的 sandbox 區塊與 OWNERSHIP.yaml 不符")
                bad += 1
        else:
            st["sandbox"] = want
            f.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if a.verify:
        if bad:
            print(f"sync_sandbox：{bad} 個 Agent 的沙箱設定過期（跑 `python scripts/sync_sandbox.py`）")
            return 1
        print(f"sync_sandbox：{len(agents)} 個 Agent 的沙箱設定與 OWNERSHIP.yaml 一致")
        return 0

    print(f"sync_sandbox：已由 OWNERSHIP.yaml 生成 {len(agents)} 份 sandbox 設定")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
