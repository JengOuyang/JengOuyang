---
name: blind-review
description: REDTEAM 盲審流程
---

# blind-review

## 何時使用
REDTEAM 盲審流程。

## 輸入 / 輸出契約
- **輸入**：Router 產生的盲審包（結論 + 資料切片，無 reasoning）
- **輸出**：`REVIEW_RESULT{verdict, independent_read, findings[]}`
- **失敗時**：無法從資料重建結論 → 這本身就是 finding，標 HIGH

## 步驟
1. 只讀 Router 給的盲審包（結論 + 資料切片）；先獨立重建結論。
2. 對照差異 → findings（severity、evidence、suggestion）。
3. verdict 三選一；DISAGREE 必須可驗證。
4. 回測審核：重跑 --verify。

## 完成檢查
- [ ] independent_read 非空
- [ ] DISAGREE 有證據

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/blind_pack.py（Router 端）`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
