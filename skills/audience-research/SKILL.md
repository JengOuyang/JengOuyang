---
name: audience-research
description: 客戶分析：留言／私訊主題分群與 Persona 修正（去識別化）
---

# audience-research

## 何時使用
客戶分析：留言／私訊主題分群與 Persona 修正（去識別化）。

## 輸入 / 輸出契約
- **輸入**：去識別化的留言／私訊文字
- **輸出**：`[{theme, count, pain_point, content_idea}]` + Persona 修正建議
- **失敗時**：樣本 < 20 則 → 標為初步觀察，寫入 knowledge 時 status=UNVERIFIED

## 步驟
1. 匯出留言／私訊文字（去除帳號與個資）；主題分群（痛點、問題、需求）。
2. 對照 Persona P1–P3；提出修正與內容建議。
3. 不儲存個人可識別資料。

## 完成檢查
- [ ] 去識別化

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/comments_export.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
