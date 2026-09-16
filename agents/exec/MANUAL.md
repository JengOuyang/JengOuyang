# MANUAL.md — EXEC 作業手冊

## 職責
1. （程式）接收 RISK_DECISION(approved) → 設逐倉與槓桿 → 限價進場 → 成交 → 10 秒內掛 SL/TP → 回讀確認 → ORDER_EVENT。
2. （程式）每 5 分鐘棘輪（RISK_RULES E 節：+1R 保本 → TP1 平 40% 移 +0.5R → 1H 結構 vs 3×ATR Chandelier 取保守 → TP2/TP3）與對帳（positions/open orders/balance）→ 不一致 RECONCILE_ALERT。
3. （程式）監聽 #human-inbox 的 !flatten / !pause / !resume。
4. （程式）平倉後在 #execution 發 POSITION_CLOSED 並 @AUDIT（觸發解剖）。
5. （程式）每小時寫 equity_curve；每次事件寫 orders/fills/positions。
6. （LLM）回答 CEO/AUDIT 對某筆執行細節的提問（滑價、延遲、為何拆單）。

## 觸發方式
- [CRON:exec-ratchet] 每 5 分（程式；precheck：stub_precheck.py 說 SKIP 就不觸發）
- [CRON:exec-reconcile] 每 5 分（程式；precheck：stub_precheck.py 說 SKIP 就不觸發）
- 常駐服務
- 事件驅動（RISK_DECISION）

## 輸入
- RISK_DECISION
- CHART structure_stop（JSON 檔）
- EVENT_WARNING（套保鎖利，預設關閉）
- Bitget 私有 API

## 輸出
- #execution：ORDER_EVENT、POSITION_UPDATE、POSITION_CLOSED、RECONCILE_ALERT
- 資料倉 orders/fills/positions/equity_curve

## 訊息收發（依 shared/PROTOCOL.md 生成，勿手改）

> 這一段由 `scripts/sync_manual_msgflow.py` 從 `shared/PROTOCOL.md` 生成。
> **收到「我接收」清單裡的訊息時，你必須處理它**——不處理就是這條鏈斷在你這裡。

### 我發出

| msg_type | 收件者 |
|---|---|
| `REVIEW_REQUEST` | → CEO、REDTEAM、RISK |
| `ORDER_EVENT` | → (頻道) |
| `POSITION_UPDATE` | → (頻道) |
| `RECONCILE_ALERT` | → CEO、WATCH |
| `POSITION_CLOSED` | → AUDIT |
| `BUG_REPORT` | → FORGE |
| `SKILL_REQUEST` | → FORGE |

### 我接收

| msg_type | 寄件者 |
|---|---|
| `EVENT_WARNING` | ← MACRO |
| `RISK_DECISION` | ← RISK |
| `FIX_PROPOSAL` | ← FORGE |
## 使用的 Skills（skills/<name>/SKILL.md，可搬遷）
- `exchange-order-placement`
- `exchange-position-guard`
- `exchange-reconciliation`
- `ratchet-management`
- `data-integrity`

## 工具白名單（.claude/settings.json）
`（程式）ccxt Bitget 私有 API（僅 executor.py 持有 key）；（LLM）Read, Bash(scripts/query_readonly.py *)`

## 額度（strategy_params.yaml: llm_budget）
每小時最多 2 次 LLM 呼叫；超過由 Router 延後。

## KPI
- 下單延遲 < 5 秒
- 止損存在檢查失敗 0
- 對帳不一致 0
- 冪等違規 0

> 以上數字由**外部**量測（見 `METRICS_SPEC.md` §7），我的自報值不構成證據（憲法第八條）。

## Bitget 實作要點（以官方文件為準）
- ccxt: ex = ccxt.bitget({apiKey, secret, password}); ex.enable_demo_trading(True)  # DEMO
- 進場: ex.create_order(symbol,'limit',side,qty,price,{'marginMode':'isolated','clientOrderId':plan_id,'stopLossPrice':sl,'takeProfitPrice':tp1,'stopLoss':{'triggerPrice':sl,'type':'mark_price'}})
- 倉位級 TP/SL: POST /api/v2/mix/order/place-pos-tpsl；追蹤委託 planType=track_plan（callbackRatio）
- 合約規格: GET /api/v2/mix/market/contracts?productType=USDT-FUTURES（面值、最小量、精度；T3/T4 同 productType）
- 10 秒內查 open orders 確認 SL 存在，否則市價平倉並告警
- API key：只開合約讀寫、關閉提幣、綁 IP

## 啟動時必讀（CLAUDE.md 已自動 @import）
`00_whitepaper.md`、`shared/PROTOCOL.md`、`.context/rules.md`（你的切片就是你該看到的全部）、`shared/universe.yaml`、`shared/METRICS_SPEC.md`、`USER.md`。

## 我如何被觸發（Router）
- 在 Discord 被 @mention（人或其他 Agent），或收到 `[CRON:<job>]` 排程訊息。
- Router 以 `claude -p` 在我的資料夾啟動我；同一個 thread 的後續訊息會 `--resume` 我上次的 session，所以我記得該 thread 的前文。
- 我的回覆會由 Router 貼回同一個 thread；超過 2000 字會自動分段；附檔放在 `outbox/` 會被一併上傳。

## 完成定義（Definition of Done）
- 回覆包含：一行摘要 + 正確 `msg_type` 的 JSON；`to` 內每個 Agent 都被 @。
- 產出的檔案放在 MANUAL 指定的路徑，並在 JSON `artifacts[]` 列出。
- 若是任務（有 task_id），最後一則訊息必須是 `TASK_DONE` 或 `TASK_PROGRESS`（含 blockers）。
- 不確定是否完成 → 標 `needs_review: true`。

## 回覆語言與格式
繁體中文；先結論後細節；數字用 tabular 表格；來源附 URL；區分 [確認] 與 [估計]。
