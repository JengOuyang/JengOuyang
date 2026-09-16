#!/usr/bin/env python3
"""sync_manual_msgflow.py — 依 shared/PROTOCOL.md 為每份 MANUAL 生成「訊息收發」段落。

存在的理由：稽核發現 35 個破口——`REGIME_REPORT` 兩端手冊都沒寫、`RECONCILE_ALERT` 沒有收件方、
`RISK_SIGNOFF` 寄件方自己不知道要發。PROTOCOL.md 的 msg_type 表是單一真相，
手抄到 15 份手冊必然漏，所以改成生成。

用法：
    python scripts/sync_manual_msgflow.py            # 重寫所有 MANUAL 的該段落
    python scripts/sync_manual_msgflow.py --verify   # 只檢查（lint 第 17 項用）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
SECTION = "## 訊息收發（依 shared/PROTOCOL.md 生成，勿手改）"
# PROTOCOL 表格裡的非 Agent 字樣
NON_AGENT = {"(頻道)", "全員", "任何", "Owner", "主持者", "被派工者", "審核者", "原發送者", "publisher 程式"}


def parse_protocol() -> list[tuple[str, str, str]]:
    text = (ROOT / "shared" / "PROTOCOL.md").read_text(encoding="utf-8")
    return re.findall(r"^\| ([A-Z][A-Z_]+) \| ([^|]+) \| ([^|]+) \|", text, re.M)


def agents_in(cell: str, all_agents: list[str]) -> list[str]:
    return [a for a in all_agents if re.search(rf"\b{a.upper()}\b", cell.upper())]


def build(agent: str, rows, all_agents) -> str:
    out_rows, in_rows = [], []
    for mt, sender, receiver in rows:
        s_agents, r_agents = agents_in(sender, all_agents), agents_in(receiver, all_agents)
        broadcast = any(k in sender for k in ("任何", "全員"))
        if agent in s_agents or broadcast:
            to = "、".join(x.upper() for x in r_agents) or receiver.strip()
            out_rows.append(f"| `{mt}` | → {to} |")
        if agent in r_agents:
            frm = "、".join(x.upper() for x in s_agents) or sender.strip()
            in_rows.append(f"| `{mt}` | ← {frm} |")

    L = [SECTION, "",
         "> 這一段由 `scripts/sync_manual_msgflow.py` 從 `shared/PROTOCOL.md` 生成。",
         "> **收到「我接收」清單裡的訊息時，你必須處理它**——不處理就是這條鏈斷在你這裡。", ""]
    L += ["### 我發出", "", "| msg_type | 收件者 |", "|---|---|"] + (out_rows or ["| —（無） | |"]) + [""]
    L += ["### 我接收", "", "| msg_type | 寄件者 |", "|---|---|"] + (in_rows or ["| —（無） | |"]) + [""]
    return "\n".join(L)


def sync(write: bool) -> int:
    rows = parse_protocol()
    all_agents = sorted(d.name for d in (ROOT / "agents").iterdir() if d.is_dir() and (d / "MANUAL.md").exists())
    problems, changed = [], []

    for agent in all_agents:
        m = ROOT / "agents" / agent / "MANUAL.md"
        text = m.read_text(encoding="utf-8")
        want = build(agent, rows, all_agents)

        if SECTION in text:
            head, _, tail = text.partition(SECTION)
            _, sep, rest = tail.partition("\n## ")
            new = head + want + (("## " + rest) if sep else "")
        else:                                     # 插在「## 使用的 Skills」之前，否則附加在檔尾
            anchor = "## 使用的 Skills"
            new = text.replace(anchor, want + anchor, 1) if anchor in text else text.rstrip() + "\n\n" + want

        if new == text:
            continue
        if write:
            m.write_text(new, encoding="utf-8")
            changed.append(agent)
        else:
            problems.append(f"{agent}/MANUAL.md 的訊息收發段落與 PROTOCOL.md 不符")

    if write:
        print(f"sync_manual_msgflow：更新 {len(changed)} 份手冊" + (f"（{', '.join(changed)}）" if changed else ""))
    for p in problems:
        print("  ERROR", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(sync(write="--verify" not in sys.argv))
