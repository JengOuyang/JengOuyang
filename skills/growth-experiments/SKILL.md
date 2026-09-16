---
name: growth-experiments
description: 設計、追蹤與判讀行銷 A/B 實驗（發文時間、封面樣式、hook 句型、hashtag 組）時使用
---

# growth-experiments

## 何時使用
要驗證某個內容假設是否成立。

## 輸入 / 輸出契約
- **輸入**：`v_content_metrics`、`v_ig_insights_daily`
- **輸出**：`{name, hypothesis, metric, n, result, decision}` + `knowledge` 表一列
- **失敗時**：樣本不足就明說「尚無結論」，不要用趨勢當證據

## 步驟
1. 寫下假設：「改變 X 會讓 Y 提升 Z%」。**一次只變一個變數**。
2. 決定判定指標（通常是 save_rate 或 engagement_rate）與最小樣本數（≥ 6 篇）。
3. 設定對照組與實驗組，記錄在 `marketing/analytics/`。
4. 樣本收齊後才判讀；未達樣本數就宣稱結論是最常見的錯誤。
5. 結論寫進 `knowledge` 表，**status 一律先標 `UNVERIFIED`**；重複驗證後才升級 `VALIDATED`。
6. 把可採用的結論交給 CMO 更新內容行事曆。

## 完成檢查
- [ ] 一次一變數
- [ ] 樣本數有標註
- [ ] 結論寫進 knowledge 表且標了 status

## 相關程式
- `engine/marketing_metrics.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
