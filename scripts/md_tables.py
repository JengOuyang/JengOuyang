#!/usr/bin/env python3
"""md_tables.py — Markdown 表格的結構檢查（lint 第 22 項與 build_site 共用）。

抽成獨立模組的理由：v3.0.5 之前這段住在 build_site.py，而 build_site.py 是頂層腳本——
lint `from build_site import orphan_table_rows` 會**順便把整個站台重建一次**。
使用者看到的症狀是跑 lint 卻冒出「已產生 ... TRADE-DESK_whitepaper.html」。

兩種會讓表格印不出來的寫法都抓：
  1. 孤兒列：`| a | b |` 前後沒有表頭與分隔列
  2. 表頭緊接段落：Markdown 會把它吸進上一個段落，印出裸的 | 字元
"""
from __future__ import annotations

import re
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台）


# ── 結構檢查：孤兒表格列 ──────────────────────────────────────────
def orphan_table_rows(md: str) -> list[tuple[int, str]]:
    """找出不屬於任何表格的 `| ... |` 行。

    合法的表格列，往上追到第一個非表格行之前，必須出現過分隔列（|---|---|）。
    """
    bad, lines = [], md.splitlines()
    in_fence = False
    seen_sep = False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = line.strip()
        is_row = s.startswith("|") and s.endswith("|") and s.count("|") >= 3
        if not is_row:
            seen_sep = False
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", s):        # 分隔列
            seen_sep = True
            continue
        if not seen_sep:
            # 下一行是分隔列 → 這是表頭，合法
            nxt = lines[i].strip() if i < len(lines) else ""
            if not re.fullmatch(r"\|[\s:|-]+\|", nxt):
                bad.append((i, "孤兒列（不屬於任何表格）：" + s[:70]))
            else:
                # 表頭若緊接在「段落」之後，會被 Markdown 吸進那個段落而不成表格。
                # 接在標題、清單、引言、分隔線或空行之後都沒問題。
                prev = lines[i - 2].strip() if i >= 2 else ""
                if prev and not re.match(r"^(#{1,6}\s|[-*+]\s|\d+\.\s|>|---|\|)", prev):
                    bad.append((i, "表頭緊接段落，需空一行：" + s[:70]))
    return bad


def check_tables(md: str, name: str) -> int:
    bad = orphan_table_rows(md)
    if bad:
        print(f"🛑 {name}：{len(bad)} 個孤兒表格列（會被印成裸的 | 字元）")
        for ln, txt in bad:
            print(f"   第 {ln} 行：{txt}")
        return 1
    return 0



def check_all_docs() -> int:
    """--check：掃 docs/ 與 shared/ 的所有 Markdown 表格結構。lint 第 22 項用這個。"""
    bad = 0
    for f in sorted(Path(ROOT).glob("docs/*.md")) + sorted(Path(ROOT).glob("shared/*.md")):
        bad += check_tables(f.read_text(encoding="utf-8"), f.name)
    if bad:
        return 1
    print("全部文件的表格結構正常")
    return 0


