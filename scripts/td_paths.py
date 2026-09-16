#!/usr/bin/env python3
"""td_paths.py — 「哪些檔案算是這個專案自己的」的單一定義。

為什麼需要它：
    v3.0.5 的 lint 第 24 項用 `ROOT.rglob("*.py")` 掃全樹比對 requirements.txt。
    我的環境沒有 `.venv`，所以一直是綠的；使用者一建好虛擬環境，
    它就開始檢查 pandas、pip 自己的原始碼，噴出 163 個錯：

        ERROR [24] .venv\\Lib\\site-packages\\pandas\\io\\clipboard\\__init__.py
                   import 了 `AppKit`，但 requirements.txt 沒有它

    任何「掃全樹」的檢查都會踩同一個坑，所以排除清單只能有一份。

用法：
    from td_paths import project_py_files, is_project_file
    for f in project_py_files(ROOT): ...
"""
from __future__ import annotations

from pathlib import Path

# 這些目錄底下的東西不是我們寫的，或是生成物
EXCLUDED_DIRS = {
    ".venv", "venv", "env", ".env",            # 虛擬環境
    "site-packages", "dist-packages",          # 第三方套件
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".idea", ".vscode",
    "node_modules",
    "worktree",                                # FORGE 的沙箱（是 main 的副本）
    "build", "dist", ".eggs",
    "legacy",                                  # 舊專案盤點的掛載點，不是本專案的碼
    "data", "logs",                            # 執行期產物
}


def is_project_file(path: Path, root: Path) -> bool:
    """這個檔案是不是「這個專案自己寫的」。"""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return not any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in rel.parts)


def project_py_files(root: Path) -> list[Path]:
    """專案自己的 .py，排序後回傳。"""
    return sorted(f for f in root.rglob("*.py") if f.is_file() and is_project_file(f, root))
