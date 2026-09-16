---
name: exchange-reconciliation
description: 每 5 分鐘核對本地帳與交易所實際部位、掛單、餘額時使用
---

# exchange-reconciliation

## 何時使用
定期對帳，或懷疑本地狀態與交易所不一致時。

## 輸入 / 輸出契約
- **輸入**：交易所 API 的即時狀態 + 資料倉的本地紀錄
- **輸出**：`{matched: bool, diffs: [...]}` 與新的 positions 快照
- **失敗時**：不一致時停開新單並告警；**絕不自動調整帳務**

## 步驟
1. 拉交易所的 positions / open orders / balance。
2. 與資料倉的 `v_open_positions`、`v_open_orders`、`equity_curve` 逐項比對。
3. 差異分類：數量不符 / 有倉無單 / 有單無倉 / 餘額偏差 > 0.5%。
4. 任一不符 → `RECONCILE_ALERT` 並依 RISK_RULES C7 停開新單（不自動修正，因為自動修正可能把錯的變成對的）。
5. 寫入 `positions` 快照，供 Dashboard 與 AUDIT 使用。

## 完成檢查
- [ ] 有倉無止損單會被抓到
- [ ] 差異有分類不是只說「不一致」
- [ ] 不會自動修改資料

## 相關程式
- `engine/executor.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
