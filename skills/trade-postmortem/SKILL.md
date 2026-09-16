---
name: trade-postmortem
description: AUDIT 每筆交易解剖與止損原因分類
---

# trade-postmortem

## 何時使用
AUDIT 每筆交易解剖與止損原因分類。

## 輸入 / 輸出契約
- **輸入**：plan、risk_decision、fills、該期間 ohlcv
- **輸出**：通過 `trade_journal.schema.json` 的 TradeReview
- **失敗時**：資料不足以判斷止損原因 → 標 `DATA_ISSUE` 而不是猜一個類別

## 步驟
1. 取 plan、decision、fills、1H K 線；算 R_net、MAE/MFE、滑價、持倉時間。
2. exit_reason 與 stop_reason（10 類）分類，附證據。
3. what_went_right/wrong；improvements 含 testable_hypothesis。
4. needs_followup → 建議 CEO 立項給 LAB。

## 完成檢查
- [ ] schema 合格
- [ ] 分類有證據

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/write_review.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
