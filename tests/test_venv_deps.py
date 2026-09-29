"""test_venv_deps.py — 確認 .venv 同步與啟動腳本包含依賴同步呼叫。

防止 BUG_20260926_0710 / BUG_20260929_1820 / BUG_20260930_0000 的迴歸：
  requirements.txt 加新套件後，start.ps1 / watchdog.ps1 必須在啟動前自動 pip install。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_httpx_importable() -> None:
    """httpx 必須在當前 Python 環境可 import（venv 必須已同步 requirements.txt）。"""
    spec = importlib.util.find_spec("httpx")
    assert spec is not None, (
        "httpx 未安裝——請執行 .venv\\Scripts\\pip.exe install -r requirements.txt 同步 .venv。"
        "（根因：BUG_20260926_0710 / BUG_20260929_1820 / BUG_20260930_0000）"
    )


def test_start_ps1_calls_pip_install() -> None:
    """start.ps1 必須在啟動 Router 前以 PowerShell 呼叫 pip install（防 venv 漂移）。"""
    text = (ROOT / "router" / "start.ps1").read_text(encoding="utf-8")
    assert "pip" in text and "requirements.txt" in text, (
        "router/start.ps1 未呼叫 pip install——新套件加入 requirements.txt 後 venv 不會自動更新。"
    )


def test_watchdog_ps1_calls_pip_install() -> None:
    """watchdog.ps1 重啟前必須執行 pip install（防 venv 漂移）。"""
    text = (ROOT / "router" / "watchdog.ps1").read_text(encoding="utf-8")
    assert "pip" in text and "requirements.txt" in text, (
        "router/watchdog.ps1 未在重啟前 pip install——新套件加入後 watchdog 重啟仍會失敗。"
    )
