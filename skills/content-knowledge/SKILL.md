---
name: content-knowledge
description: 教育貼文知識庫（SMC、風控、凱利、棘輪、總經概念）
---

# content-knowledge

## 何時使用
教育貼文知識庫（SMC、風控、凱利、棘輪、總經概念）。

## 輸入 / 輸出契約
- **輸入**：要解釋的概念名稱
- **輸出**：`{定義, 例子, 常見誤區, 配圖構想}`
- **失敗時**：概念超出 shared/ 已定義的範圍 → 標為待確認，不要自行發明定義

## 步驟
1. 每個概念：一句定義、一個例子、一個常見誤區、一張圖的構想。
2. 來源：本專案 shared/RISK_RULES、smc-analysis skill。
3. 維護於 skills/content-knowledge/topics/*.md。

## 完成檢查
- [ ] 概念準確
- [ ] 無投資建議

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- （純知識型技能，無程式）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
