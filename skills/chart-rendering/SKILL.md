---
name: chart-rendering
description: 以程式產出盤面圖（K 線 + 關鍵區）供內容與審核使用
---

# chart-rendering

## 何時使用
以程式產出盤面圖（K 線 + 關鍵區）供內容與審核使用。

## 輸入 / 輸出契約
- **輸入**：`v_market` / `v_levels` 的資料範圍
- **輸出**：PNG/JPG 圖檔（**不得含進場價、止損、倉位**）
- **失敗時**：資料不足以畫出有意義的圖 → 不產圖並說明

## 步驟
1. mplfinance/plotly 讀 ohlcv + levels（OB/FVG/POC/Fib）繪圖；深色品牌樣式；不顯示進場價。
2. 輸出 PNG/JPG 至 outbox/ 或 marketing/queue/。

## 完成檢查
- [ ] 無進場價

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/render_chart.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
