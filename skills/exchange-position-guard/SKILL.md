---
name: exchange-position-guard
description: 進場成交後掛倉位級止損止盈並驗證其存在（10 秒規則）時使用
---

# exchange-position-guard

## 何時使用
有部位成交，必須在 10 秒內確保交易所端有止損單。這是整個系統最不可妥協的一條。

## 輸入 / 輸出契約
- **輸入**：成交事件（fill）與該 plan 的 stop_loss / take_profit[]
- **輸出**：已確認存在的 SL/TP order_id，寫入 `positions.sl_price`、`tp_prices_json`
- **失敗時**：確認失敗 → 市價平倉 + P0 告警，不重試、不等待

## 步驟
1. 成交回報進來的當下就掛倉位級 SL/TP：`POST /api/v2/mix/order/place-pos-tpsl`（或 ccxt 的 `stopLossPrice`/`takeProfitPrice`）。
2. 觸發價一律用 **mark_price**，避免插針掃損。SL 用市價單，TP 用限價單。
3. 掛完**回讀** open orders 確認止損單真的存在。
4. 若 10 秒內確認不到止損單 → **立刻市價平倉**並在 `#alerts` 告警。沒有止損的部位不允許存在。
5. 把 SL/TP 的 order_id 寫入 `positions`，交給 ratchet-management 後續調整。

## 完成檢查
- [ ] 觸發價用 mark_price
- [ ] 回讀確認過止損存在
- [ ] 逾時走的是平倉而不是重試

## 相關程式
- `engine/executor.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
