---
name: seo-keywords
description: 關鍵字與話題研究（Google Trends、Search Console、IG 搜尋）
---

# seo-keywords

## 何時使用
關鍵字與話題研究（Google Trends、Search Console、IG 搜尋）。

## 輸入 / 輸出契約
- **輸入**：Google Trends / Search Console / IG hashtag 資料
- **輸出**：題材清單 `[{term, trend, intent, suggested_pillar, source, date}]`
- **失敗時**：資料源失效 → 標註缺漏來源，不要用舊資料冒充當期

## 步驟
1. scripts/trends.py（pytrends）：加密／黃金／美股熱詞、相關查詢上升榜。
2. scripts/gsc.py（若有網站）：查詢、點擊、排名。
3. IG：hashtag 貼文數與最近貼文互動；競品標籤。
4. 輸出題材清單（term、trend、意圖、建議支柱）。

## 完成檢查
- [ ] 來源與日期

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/trends.py`
- `scripts/gsc.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
