---
name: exchange-order-placement
description: 在 Bitget USDT-M 永續冪等下單（限價進場、區間拆單、槓桿與保證金模式）時使用
---

# exchange-order-placement

## 何時使用
收到 RISK 核准的 ApprovedOrder，需要把它變成交易所的實際掛單。

## 輸入 / 輸出契約
- **輸入**：ApprovedOrder（`shared/schemas/risk_decision.schema.json` 的 approved=true 記錄）
- **輸出**：`{order_id, client_oid, price, qty, status}`，並寫入 `orders` 表
- **失敗時**：下單失敗回傳明確錯誤碼；連續 3 次失敗觸發 RISK_RULES C7（停開新單）

## 步驟
1. 讀 ApprovedOrder：symbol、side、qty、entry、leverage、plan_id。
2. 查合約規格 `GET /api/v2/mix/market/contracts?productType=USDT-FUTURES`：面值、最小量、價格與數量精度；四層宇宙都用同一個 productType，但精度不同。
3. 設定逐倉與槓桿（先查現況，相同就不重設，避免多餘 API 呼叫）。
4. `clientOrderId = plan_id` 下限價單（GTC）。ZONE 型進場拆兩筆，各半量。
5. **下單前先用 clientOrderId 查詢是否已存在**——這是冪等的唯一保證，重送不會變成兩倉。
6. 回傳 order_id 與實際掛單參數，交給 exchange-position-guard 接手。

## 完成檢查
- [ ] clientOrderId 等於 plan_id
- [ ] 重送同一 plan 不會產生第二筆單
- [ ] qty 與 price 符合合約精度

## 相關程式
- `engine/bitget_client.py`
- `engine/executor.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
