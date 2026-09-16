# ADR-001：用自寫 Discord Router，而非官方 Channels plugin

狀態：**採納** · 日期 2026-09-08 · 決策者 Owner

## 背景
15 個 Agent 需要在 Discord 上即時收發訊息。Claude Code 官方提供 Channels（研究預覽），可把 Discord 訊息推進一個正在執行的 session。

## 選項
| 方案 | 優點 | 缺點 |
|---|---|---|
| A. 官方 Channels plugin | 官方支援、設定簡單、互動式串流 | 一個 session 一隻 Bot，15 個 Agent 要開 15 個互動視窗；無佇列、無額度控制、無排程；研究預覽期介面可能變動 |
| B. 自寫 Router + `claude -p` | 佇列、並行控制、每 Agent 額度、排程、狀態表情、稽核紀錄、可熱重載設定 | 要自己維護約 300 行程式；失去互動式串流 |
| C. Agent SDK 寫常駐服務 | 最大彈性 | 需另計費用模式風險；開發量最大 |

## 決定
選 **B**。理由：
- Claude Pro 額度有限，**必須**有佇列與每 Agent 上限，這是 A 做不到的。
- 排程要能「以 Discord 訊息觸發」才能滿足「所有溝通留紀錄」的要求。
- `claude -p` 目前計入訂閱一般用量（Anthropic 2026-06-15 暫停另計 Agent SDK 額度的方案）。

失去的互動串流用 👀（收到）→ ⚙️（處理中）→ ✅／❌ 的表情回饋補上，手機上也看得到進度。

## 後果
- 需維護 `router/discord_router.py`；Router 掛掉全隊停擺 → 用 `watchdog.ps1` 每 5 分鐘重啟。
- 你仍可另開一個互動視窗用官方 Channels 跟 CEO 聊天，那是加分項不是主幹。

## 何時重新考慮
Channels 正式版若支援「一個 process 多 Bot + 佇列」，或 Agent 數量超過單機負荷需要分散式。
