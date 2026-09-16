#!/usr/bin/env python3
"""
render_chart.py — 純程式圖片產生器，輸出 1080×1350 JPG。

支援模板（--template）：
  td-edu        : 教育貼文（文字 + 表格版型）
  td-daily-chart: 盤面圖（K 線 + 關鍵區）—— 需 SQLite 行情資料
  td-daily-macro: 總經 brief 摘要圖
  td-weekly     : 週回顧圖

用法：
  # 教育貼文
  python scripts/render_chart.py \\
      --template td-edu \\
      --meta marketing/queue/2026-09-16/c_20260916_edu_risk/meta.json \\
      --out marketing/queue/2026-09-16/c_20260916_edu_risk/

  # K 線圖（需 TD_DB）
  python scripts/render_chart.py \\
      --template td-daily-chart \\
      --symbol BTCUSDT \\
      --tf 4h \\
      --out outbox/

輸出：<out>/<content_id>_slide_N.jpg（教育）或 <out>/<symbol>_<tf>_chart.jpg
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]

# ── 品牌設定（更新此處即全域生效） ───────────────────────────────────────────
BRAND = {
    "bg":        "#0D1117",   # 深色底
    "surface":   "#161B22",   # 卡片底色
    "accent":    "#F0B429",   # 金黃主色
    "danger":    "#E05252",   # 警示紅
    "success":   "#3FB950",   # 成功綠
    "text":      "#E6EDF3",   # 主文字
    "subtext":   "#8B949E",   # 次要文字
    "border":    "#30363D",   # 邊框
    "watermark": "TRADE-DESK",
    "disclaimer": "本內容僅為市場觀察與教育分享，非投資建議；交易有風險。",
    "img_w": 1080,
    "img_h": 1350,
}


def _hex(color: str):
    """Convert '#RRGGBB' to (R, G, B) 0-255 tuple."""
    c = color.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def _ensure_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        sys.exit(
            "ERROR: Pillow 未安裝。請執行：pip install Pillow\n"
            "（若有 mplfinance 需求亦安裝：pip install mplfinance pandas）"
        )


def _get_font(ImageFont, size: int, bold: bool = False):
    """嘗試載入系統中文字型，fallback 到預設字型。"""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/msjhbd.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux / Noto
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
    ]
    if bold:
        candidates = [
            "C:/Windows/Fonts/msjhbd.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
        ] + candidates
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_watermark(draw, ImageFont, w: int, h: int):
    font = _get_font(ImageFont, 22)
    draw.text((24, 24), BRAND["watermark"], font=font, fill=_hex(BRAND["accent"]))


def _draw_date(draw, ImageFont, w: int, h: int, date_str: str = ""):
    font = _get_font(ImageFont, 22)
    date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bbox = draw.textbbox((0, 0), date_str, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((w - tw - 24, 24), date_str, font=font, fill=_hex(BRAND["subtext"]))


def _draw_disclaimer(draw, ImageFont, w: int, h: int):
    font = _get_font(ImageFont, 20)
    text = BRAND["disclaimer"]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    draw.text((x, h - 40), text, font=font, fill=_hex(BRAND["subtext"]))


def _draw_progress_dots(draw, w: int, y: int, current: int, total: int):
    """底部換頁圓點。"""
    dot_r = 6
    gap = 20
    total_w = total * (dot_r * 2) + (total - 1) * gap
    x = (w - total_w) // 2
    for i in range(total):
        color = _hex(BRAND["accent"]) if i == current else _hex(BRAND["border"])
        draw.ellipse([x, y, x + dot_r * 2, y + dot_r * 2], fill=color)
        x += dot_r * 2 + gap


# ── td-edu ──────────────────────────────────────────────────────────────────

def _render_edu_cover(ImageDraw_cls, ImageFont_cls, Image_cls, meta: dict) -> "Image":
    w, h = BRAND["img_w"], BRAND["img_h"]
    img = Image_cls.new("RGB", (w, h), _hex(BRAND["bg"]))
    draw = ImageDraw_cls.Draw(img)

    topic = meta.get("topic", "")
    hook  = meta.get("hook_preview", topic)
    slides_total = meta.get("slides", 3)

    # 上半留白 + 大標題
    title_font  = _get_font(ImageFont_cls, 72, bold=True)
    sub_font    = _get_font(ImageFont_cls, 34)

    # 分行（每行最多 14 字）
    lines = _wrap_text(hook, 14)
    y = h // 2 - len(lines) * 80 // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), line, font=title_font, fill=_hex(BRAND["text"]))
        y += 88

    # 教育標籤
    tag = "📊 教育貼文"
    tag_font = _get_font(ImageFont_cls, 28)
    draw.text((w // 2 - 60, y + 30), tag, font=tag_font, fill=_hex(BRAND["accent"]))

    # slide N / total
    slide_font = _get_font(ImageFont_cls, 26)
    draw.text((w // 2 - 20, h - 100), f"1 / {slides_total}", font=slide_font, fill=_hex(BRAND["subtext"]))

    _draw_watermark(draw, ImageFont_cls, w, h)
    _draw_date(draw, ImageFont_cls, w, h, meta.get("scheduled_for", "")[:10])
    _draw_disclaimer(draw, ImageFont_cls, w, h)
    return img


def _render_edu_table(ImageDraw_cls, ImageFont_cls, Image_cls, meta: dict, slide_idx: int) -> "Image":
    """Slide 2：數據比較表（從 meta 的 slide_descriptions 或 caption 萃取）。"""
    w, h = BRAND["img_w"], BRAND["img_h"]
    img = Image_cls.new("RGB", (w, h), _hex(BRAND["bg"]))
    draw = ImageDraw_cls.Draw(img)

    slides_total = meta.get("slides", 3)

    # 硬編教育數據（連虧模型）——若 meta 有 table_data 則覆蓋
    table_data = meta.get("table_data", [
        ["單筆風險", "剩餘本金", "回本需漲"],
        ["10%",      "34.9%",   "+186%"],
        ["5%",       "59.9%",   "+67%"],
        ["2%",       "81.7%",   "+22%"],
        ["1.5% ✓",  "85.9%",   "+16%"],
    ])

    title_font = _get_font(ImageFont_cls, 44, bold=True)
    header_font = _get_font(ImageFont_cls, 30, bold=True)
    cell_font  = _get_font(ImageFont_cls, 34)

    subtitle = "連虧 10 筆後帳戶剩多少？"
    bbox = draw.textbbox((0, 0), subtitle, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, 80), subtitle, font=title_font, fill=_hex(BRAND["text"]))

    # 表格
    cols = len(table_data[0])
    rows = len(table_data)
    col_w = (w - 80) // cols
    row_h = 90
    table_top = 200

    for r, row in enumerate(table_data):
        for c, cell in enumerate(row):
            x0 = 40 + c * col_w
            y0 = table_top + r * row_h
            x1 = x0 + col_w
            y1 = y0 + row_h

            # 背景
            if r == 0:
                fill = _hex(BRAND["surface"])
            elif "✓" in cell or (r == rows - 1 and c == 0):
                fill = (*_hex(BRAND["accent"]), 40)  # 高亮行用不透明純色替代
                fill = _hex("#1F2A1A")
            elif r % 2 == 0:
                fill = _hex(BRAND["surface"])
            else:
                fill = _hex(BRAND["bg"])

            draw.rectangle([x0, y0, x1, y1], fill=fill)
            draw.rectangle([x0, y0, x1, y1], outline=_hex(BRAND["border"]), width=1)

            # 文字顏色
            if r == 0:
                color = _hex(BRAND["subtext"])
                font = header_font
            elif "✓" in cell or (r == rows - 1):
                color = _hex(BRAND["accent"])
                font = cell_font
            elif r == 1 and c != 0:
                color = _hex(BRAND["danger"])
                font = cell_font
            else:
                color = _hex(BRAND["text"])
                font = cell_font

            bbox = draw.textbbox((0, 0), cell, font=font)
            tw2 = bbox[2] - bbox[0]
            th2 = bbox[3] - bbox[1]
            draw.text((x0 + (col_w - tw2) // 2, y0 + (row_h - th2) // 2), cell, font=font, fill=color)

    _draw_progress_dots(draw, w, table_top + rows * row_h + 40, slide_idx, slides_total)
    _draw_watermark(draw, ImageFont_cls, w, h)
    _draw_date(draw, ImageFont_cls, w, h, meta.get("scheduled_for", "")[:10])
    _draw_disclaimer(draw, ImageFont_cls, w, h)
    return img


def _render_edu_conclusion(ImageDraw_cls, ImageFont_cls, Image_cls, meta: dict, slide_idx: int) -> "Image":
    w, h = BRAND["img_w"], BRAND["img_h"]
    img = Image_cls.new("RGB", (w, h), _hex(BRAND["bg"]))
    draw = ImageDraw_cls.Draw(img)

    slides_total = meta.get("slides", 3)

    conclusion = meta.get("conclusion",
        "規則寫死，\n不是膽小，\n是讓虧損\n有邊界。")
    cta = meta.get("cta", "🔖 儲存這張圖——下次想「這次就多押一點」的時候翻出來看。")

    # 中央結論大字
    body_font = _get_font(ImageFont_cls, 56, bold=True)
    cta_font  = _get_font(ImageFont_cls, 30)

    lines = conclusion.split("\n")
    y = h // 2 - len(lines) * 70 // 2

    # 左側黃色豎線裝飾
    draw.rectangle([60, y - 20, 68, y + len(lines) * 70 + 20], fill=_hex(BRAND["accent"]))

    for line in lines:
        draw.text((90, y), line, font=body_font, fill=_hex(BRAND["text"]))
        y += 72

    # CTA
    cta_lines = _wrap_text(cta, 20)
    y += 60
    for line in cta_lines:
        draw.text((60, y), line, font=cta_font, fill=_hex(BRAND["subtext"]))
        y += 42

    _draw_progress_dots(draw, w, h - 120, slide_idx, slides_total)
    _draw_watermark(draw, ImageFont_cls, w, h)
    _draw_date(draw, ImageFont_cls, w, h, meta.get("scheduled_for", "")[:10])
    _draw_disclaimer(draw, ImageFont_cls, w, h)
    return img


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """簡單中文換行：按字符數硬切。"""
    lines = []
    for paragraph in text.split("\n"):
        while len(paragraph) > max_chars:
            lines.append(paragraph[:max_chars])
            paragraph = paragraph[max_chars:]
        if paragraph:
            lines.append(paragraph)
    return lines


def render_edu(meta: dict, out_dir: Path) -> list[Path]:
    Image, ImageDraw, ImageFont = _ensure_pillow()
    content_id = meta.get("content_id", "edu_unknown")
    slides_total = meta.get("slides", 3)
    out_dir.mkdir(parents=True, exist_ok=True)
    produced = []

    slide_renderers = [
        lambda: _render_edu_cover(ImageDraw, ImageFont, Image, meta),
        lambda: _render_edu_table(ImageDraw, ImageFont, Image, meta, 1),
        lambda: _render_edu_conclusion(ImageDraw, ImageFont, Image, meta, 2),
    ]

    for i in range(min(slides_total, len(slide_renderers))):
        img = slide_renderers[i]()
        dest = out_dir / f"{content_id}_slide_{i+1}.jpg"
        img.save(str(dest), "JPEG", quality=92, optimize=True)
        produced.append(dest)
        print(f"  [slide {i+1}] → {dest}")

    return produced


# ── td-daily-chart ────────────────────────────────────────────────────────────

def render_daily_chart(symbol: str, tf: str, out_dir: Path) -> Path:
    """K 線 + 關鍵區（需要 mplfinance + pandas + SQLite 行情）。"""
    try:
        import mplfinance as mpf
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        sys.exit("ERROR: 缺少 mplfinance/pandas。請執行：pip install mplfinance pandas")

    import sqlite3

    db_path = Path(ROOT / "data" / "tradedesk.db")
    if not db_path.exists():
        sys.exit(f"ERROR: 找不到資料庫 {db_path}")

    con = sqlite3.connect(str(db_path))
    limit = {"1h": 120, "4h": 80, "1d": 90}.get(tf, 80)
    df = pd.read_sql_query(
        "SELECT ts, o, h, l, c, v FROM ohlcv "
        "WHERE symbol=? AND tf=? AND suspect=0 "
        "ORDER BY ts DESC LIMIT ?",
        con, params=(symbol, tf, limit)
    )
    con.close()

    if df.empty:
        sys.exit(f"ERROR: 查無 {symbol}/{tf} 行情資料")

    df = df.sort_values("ts").reset_index(drop=True)
    df["Date"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df = df.set_index("Date").rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})

    mc = mpf.make_marketcolors(up=BRAND["success"], down=BRAND["danger"],
                               wick={"up": BRAND["success"], "down": BRAND["danger"]},
                               volume={"up": BRAND["success"], "down": BRAND["danger"]},
                               edge="none")
    style = mpf.make_mpf_style(base_mpf_style="nightclouds",
                               marketcolors=mc,
                               facecolor=BRAND["bg"],
                               edgecolor=BRAND["border"],
                               figcolor=BRAND["bg"],
                               gridcolor=BRAND["border"])

    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{symbol}_{tf}_chart.jpg"
    fig, axes = mpf.plot(df, type="candle", style=style, volume=True,
                         title=f" {symbol} · {tf.upper()}",
                         returnfig=True, figsize=(10.8, 13.5))

    # 右下日期
    fig.text(0.96, 0.02, datetime.now(timezone.utc).strftime("%Y-%m-%d"),
             ha="right", va="bottom", color=BRAND["subtext"], fontsize=10)
    # 左上品牌
    fig.text(0.02, 0.97, BRAND["watermark"],
             ha="left", va="top", color=BRAND["accent"], fontsize=12, fontweight="bold")
    # 底部聲明
    fig.text(0.5, 0.005, BRAND["disclaimer"],
             ha="center", va="bottom", color=BRAND["subtext"], fontsize=8)

    fig.savefig(str(dest), dpi=100, bbox_inches="tight",
                facecolor=BRAND["bg"], format="jpeg")
    plt.close(fig)
    print(f"  [chart] → {dest}")
    return dest


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="TRADE-DESK 圖片產生器")
    p.add_argument("--template", required=True,
                   choices=["td-edu", "td-daily-chart", "td-daily-macro", "td-weekly"],
                   help="使用的版型")
    p.add_argument("--meta", help="meta.json 路徑（td-edu 必填）")
    p.add_argument("--symbol", help="交易對，例如 BTCUSDT（td-daily-chart 必填）")
    p.add_argument("--tf", default="4h", help="K 線時框（預設 4h）")
    p.add_argument("--out", required=True, help="輸出目錄")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.out)

    if args.template == "td-edu":
        if not args.meta:
            sys.exit("ERROR: td-edu 需要 --meta <meta.json>")
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
        paths = render_edu(meta, out_dir)
        print(json.dumps({
            "status": "ok",
            "template": "td-edu",
            "slides": len(paths),
            "files": [str(p) for p in paths],
        }, ensure_ascii=False))

    elif args.template == "td-daily-chart":
        if not args.symbol:
            sys.exit("ERROR: td-daily-chart 需要 --symbol")
        path = render_daily_chart(args.symbol, args.tf, out_dir)
        print(json.dumps({
            "status": "ok",
            "template": "td-daily-chart",
            "file": str(path),
        }, ensure_ascii=False))

    else:
        sys.exit(f"ERROR: 模板 '{args.template}' 尚未實作，請發 SKILL_REQUEST 給 FORGE")


if __name__ == "__main__":
    main()
