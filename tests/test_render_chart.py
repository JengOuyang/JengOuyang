"""
tests/test_render_chart.py — render_chart.py 的單元測試。

測試策略：
  - 不依賴 Pillow 已安裝（如未安裝則跳過圖片產出測試）
  - 驗證輔助函式（不需要 I/O）
  - 驗證 CLI 參數解析與邊界
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ── 載入模組（不執行 main） ───────────────────────────────────────────────────

def _load_render_chart():
    spec = importlib.util.spec_from_file_location(
        "render_chart", SCRIPTS_DIR / "render_chart.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rc = _load_render_chart()


# ── _hex ────────────────────────────────────────────────────────────────────

def test_hex_black():
    assert rc._hex("#000000") == (0, 0, 0)


def test_hex_white():
    assert rc._hex("#FFFFFF") == (255, 255, 255)


def test_hex_accent():
    r, g, b = rc._hex(rc.BRAND["accent"])
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255


# ── _wrap_text ───────────────────────────────────────────────────────────────

def test_wrap_short():
    lines = rc._wrap_text("短文字", 14)
    assert lines == ["短文字"]


def test_wrap_exact():
    text = "A" * 14
    lines = rc._wrap_text(text, 14)
    assert lines == [text]


def test_wrap_overflow():
    text = "A" * 15
    lines = rc._wrap_text(text, 14)
    assert len(lines) == 2
    assert lines[0] == "A" * 14
    assert lines[1] == "A"


def test_wrap_newline():
    lines = rc._wrap_text("第一行\n第二行", 20)
    assert "第一行" in lines
    assert "第二行" in lines


# ── BRAND 欄位完整性 ──────────────────────────────────────────────────────────

REQUIRED_BRAND_KEYS = [
    "bg", "surface", "accent", "danger", "success",
    "text", "subtext", "border", "watermark", "disclaimer",
    "img_w", "img_h",
]

@pytest.mark.parametrize("key", REQUIRED_BRAND_KEYS)
def test_brand_key_exists(key):
    assert key in rc.BRAND, f"BRAND 缺少 '{key}'"


def test_brand_img_size():
    assert rc.BRAND["img_w"] == 1080
    assert rc.BRAND["img_h"] == 1350


# ── render_edu（需要 Pillow）────────────────────────────────────────────────

pillow_available = importlib.util.find_spec("PIL") is not None

@pytest.mark.skipif(not pillow_available, reason="Pillow 未安裝")
def test_render_edu_produces_files(tmp_path):
    meta = {
        "content_id": "test_edu",
        "topic": "測試教育貼文",
        "hook_preview": "這是 hook 標題",
        "slides": 3,
        "scheduled_for": "2026-09-16T08:40:00+08:00",
        "disclaimer_ok": True,
    }
    paths = rc.render_edu(meta, tmp_path)
    assert len(paths) == 3
    for p in paths:
        assert p.exists(), f"期望產出 {p} 但不存在"
        assert p.stat().st_size > 10_000, f"{p} 檔案過小（可能損壞）"


@pytest.mark.skipif(not pillow_available, reason="Pillow 未安裝")
def test_render_edu_filename_pattern(tmp_path):
    meta = {
        "content_id": "c_20260916_edu_risk",
        "topic": "倉位管理測試",
        "slides": 3,
    }
    paths = rc.render_edu(meta, tmp_path)
    names = [p.name for p in paths]
    assert "c_20260916_edu_risk_slide_1.jpg" in names
    assert "c_20260916_edu_risk_slide_2.jpg" in names
    assert "c_20260916_edu_risk_slide_3.jpg" in names
