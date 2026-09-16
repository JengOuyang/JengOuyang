# Discord 伺服器：分類、頻道、可發言 Bot

| 分類 | 頻道 | env 變數 | 主要發言 Bot | 用途 |
|---|---|---|---|---|
| 🧭 指揮 | #human-inbox | CH_HUMAN_INBOX | Owner、TD-CEO、TD-EXEC(!flatten)、TD-WATCH(!budget)、TD-CREATIVE(!publish) | 你下指令與核准 |
| 🧭 指揮 | #ceo-daily | CH_CEO_DAILY | TD-CEO | 每日總匯報、HUMAN_DECISION_REQUIRED |
| 🧭 指揮 | #meeting-room | CH_MEETING_ROOM | 全員 | 盤前會、週會、事件會議（thread） |
| 🧭 指揮 | #tasks | CH_TASKS | 全員 | TASK_* 訊息 |
| 📊 交易 | #macro | CH_MACRO | TD-MACRO | MACRO_BRIEF、EVENT_WARNING |
| 📊 交易 | #market-data | CH_MARKET_DATA | TD-FEED、TD-LEDGER | 每小時快照、DATA_ALERT、UNIVERSE_UPDATE |
| 📊 交易 | #analysis | CH_ANALYSIS | TD-CHART、TD-REDTEAM、TD-RISK | HTF_CONTEXT、TRADE_PLAN、REVIEW_RESULT |
| 📊 交易 | #risk | CH_RISK | TD-RISK、TD-EXEC | RISK_DECISION、熔斷 |
| 📊 交易 | #execution | CH_EXECUTION | TD-EXEC、TD-AUDIT | ORDER_EVENT、POSITION_*、RECONCILE_ALERT |
| 📊 交易 | #journal | CH_JOURNAL | TD-AUDIT、TD-CHART | TRADE_REVIEW、日／週／月報 |
| 📊 交易 | #backtest | CH_BACKTEST | TD-LAB、TD-REDTEAM、TD-RISK | BACKTEST_REPORT、研究提案 |
| 🛠 工程 | #forge | CH_FORGE | TD-FORGE、TD-ROUTER(自動 BUG_REPORT)、TD-REDTEAM | BUG_REPORT、FIX_PROPOSAL、SKILL_* |
| 📣 行銷 | #marketing | CH_MARKETING | TD-CMO、TD-GROWTH | MARKETING_PLAN、週報 |
| 📣 行銷 | #marketing-review | CH_MARKETING_REVIEW | TD-CREATIVE、Owner | CONTENT_DRAFT 預覽、PUBLISH_REQUEST、PUBLISHED |
| 📣 行銷 | #growth | CH_GROWTH | TD-GROWTH | 每日摘要、GROWTH_REPORT、關鍵字 |
| 🔧 維運 | #agent-health | CH_AGENT_HEALTH | TD-WATCH、TD-ROUTER | 心跳、額度、⏳ 延後通知 |
| 🔧 維運 | #audit-log | CH_AUDIT_LOG | TD-LEDGER | AUDIT_ANCHOR |
| 🔧 維運 | #alerts | CH_ALERTS | 全員程式 | P0/P1 告警（會 @Owner） |

角色：`Owner`（你）、`Agents`（16 隻 Bot）。`#human-inbox` 只有 Owner 與 Agents 可發言。
