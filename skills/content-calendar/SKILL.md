---
name: content-calendar
description: 產出週內容行事曆（MARKETING_PLAN）
---

# content-calendar

## 何時使用
產出週內容行事曆（MARKETING_PLAN）。

## 輸入 / 輸出契約
- **輸入**：內容支柱、GROWTH 的最佳時段、上週成效
- **輸出**：`MARKETING_PLAN{week, calendar[], experiments[]}`
- **失敗時**：缺少素材來源（如當日無 MACRO_BRIEF）→ 該 slot 標 pending 而不是硬排

## 步驟
1. 依支柱頻率排 7 天 slot（每日 ≤ 2 篇）；最佳時段用 GROWTH 的 best_hours。
2. 每 slot：date、slot、pillar、format、audience、purpose、cta、source。
3. 包含 1 個 A/B 實驗。

## 完成檢查
- [ ] 行事曆 JSON 合法

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/write_marketing.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
