#!/usr/bin/env python3
"""把每個 Agent MANUAL.md 的「觸發方式」排程行，從 router/scheduler.yaml 重新生成。

排程表是單一真相。手抄在 15 份手冊裡的時間一定會漂掉——例如 08:00 收線那次調整，
scheduler.yaml 全改了，手冊還寫著舊時間，Agent 讀到的是錯的。

用法：
    python scripts/sync_manual_cron.py            # 重寫所有 MANUAL.md
    python scripts/sync_manual_cron.py --verify   # 只檢查，不一致回傳 1（lint 第 13 項用）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parent.parent
WEEK = ["週日", "週一", "週二", "週三", "週四", "週五", "週六"]
SECTION = "## 觸發方式"


def render_time(cron: str) -> str:
    """把 5 欄 cron 轉成手冊上的人話時間。"""
    mm, hh, dom, _mon, dow = cron.split()

    if mm.startswith("*/"):
        return f"每 {mm[2:]} 分"
    if hh.startswith("*/"):
        return f"每 {hh[2:]} 小時 :{int(mm):02d}"
    if hh == "*":
        return f"每小時 :{int(mm):02d}"

    clock = f"{int(hh):02d}:{int(mm):02d}"
    if dow != "*":
        return "、".join(WEEK[int(d)] for d in dow.split(",")) + f" {clock}"
    if dom != "*":
        days = "、".join(f"{int(d)} 日" for d in dom.split(","))
        if _mon != "*":                      # 季審是 1,4,7,10 月，不是每月
            months = "、".join(f"{int(m)}" for m in _mon.split(","))
            return f"每年 {months} 月的 {days} {clock}"
        return f"每月 {days} {clock}"
    return f"每日 {clock}"


def render_note(job: dict, agent_cfg: dict) -> str:
    """括號註記：模型、是否程式型、precheck、互斥。"""
    bits = []
    if job.get("program") or agent_cfg.get("kind") == "program":
        bits.append("程式")
    model = job.get("model")
    if model in ("opus", "haiku"):
        bits.append(model)
    if job.get("precheck"):
        bits.append(f"precheck：{Path(job['precheck'].split()[1]).name} 說 SKIP 就不觸發")
    if job.get("mutex_with"):
        bits.append(f"僅在 {job['mutex_with']} SKIP 時補跑，額度只計一次")
    return f"（{'；'.join(bits)}）" if bits else ""


def expected_lines(agent_id: str, sched: dict, cfg: dict) -> list[str]:
    agent_cfg = cfg["agents"].get(agent_id, {})
    out = []
    for j in sched["jobs"]:
        if j["agent"] != agent_id:
            continue
        out.append(f"- [CRON:{j['name']}] {render_time(j['cron'])}{render_note(j, agent_cfg)}")
    return out


def sync(write: bool) -> int:
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    problems, changed = [], []

    for manual in sorted((ROOT / "agents").glob("*/MANUAL.md")):
        agent_id = manual.parent.name
        text = manual.read_text(encoding="utf-8")
        if SECTION not in text:
            problems.append(f"{agent_id}/MANUAL.md 沒有「{SECTION}」段落")
            continue

        head, _, tail = text.partition(SECTION)
        body, sep, rest = tail.partition("\n## ")
        lines = body.splitlines()
        keep = [l for l in lines[1:] if l.strip() and not l.startswith("- [CRON:")]
        want = expected_lines(agent_id, sched, cfg)
        new_body = "\n" + "\n".join(want + keep) + "\n\n"
        new_text = head + SECTION + new_body + (("## " + rest) if sep else "")

        if new_text == text:
            continue
        if write:
            manual.write_text(new_text, encoding="utf-8")
            changed.append(agent_id)
        else:
            have = [l for l in lines if l.startswith("- [CRON:")]
            problems.append(
                f"{agent_id}/MANUAL.md 的排程與 scheduler.yaml 不符\n"
                f"      手冊：{have}\n"
                f"      應為：{want}"
            )

    if write:
        print(f"sync_manual_cron：更新 {len(changed)} 份手冊" + (f"（{', '.join(changed)}）" if changed else ""))
    for p in problems:
        print("  ERROR", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(sync(write="--verify" not in sys.argv))
