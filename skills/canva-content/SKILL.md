---
name: canva-content
description: 用 Canva MCP 依品牌模板產圖並匯出 JPG
---

# canva-content

## 何時使用
用 Canva MCP 依品牌模板產圖並匯出 JPG。

## 輸入 / 輸出契約
- **輸入**：文案 + 品牌模板 ID + 圖表 PNG
- **輸出**：1080×1350 JPG 存至 `marketing/queue/<date>/<content_id>/`
- **失敗時**：Canva MCP 失效 → 改用 `render_chart.py` 的純程式版型並 BUG_REPORT

## 步驟
1. mcp__canva：search-brand-templates／create-design-from-brand-template（或 generate-design）→ edit-design 填文字 → export-design JPG 1080×1350。
2. 模板：TD-Daily-Macro、TD-Daily-Chart、TD-Edu、TD-Weekly。
3. 圖表截圖由 scripts/render_chart.py 產生後 upload-asset。
4. 存 marketing/queue/<date>/<content_id>/。

## 完成檢查
- [ ] 尺寸正確
- [ ] 含品牌標與聲明

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/render_chart.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
