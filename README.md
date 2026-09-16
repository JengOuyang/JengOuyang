# TRADE-DESK

15 個 AI Agent 組成的量化交易與內容團隊。跑在一台 Windows 電腦上，只需要 Claude Pro + Claude Code + 一個 Discord 伺服器。

- **交易**：Bitget USDT-M 永續，四層商品宇宙（BTC/ETH → 市值前 20 → 貴金屬 → 幣股）
- **溝通**：全部走 Discord，即時（Gateway WebSocket 推送），每一步都有紀錄
- **原則**：LLM 只提案，程式才執行；資料只進不改；策略上線前要回測 8 年

## 第一次來？

| 你想做什麼 | 看哪裡 |
|---|---|
| 了解這是什麼、為什麼這樣設計 | `docs/00_WHITEPAPER.md` → `docs/01_ARCHITECTURE.md` |
| 把它建起來 | `QUICKSTART.md` → `docs/08_BUILD_PLAN.md`（**透過 CEO 指揮建置**） |
| 完整安裝細節 | `docs/02_SETUP_GUIDE.md` |
| 自己動手寫程式（備援路徑） | **`docs/04_DEV_ENVIRONMENT.md`（必讀）**，然後 `cd dev` |
| 系統跑起來後的日常 | `docs/05_OPERATIONS.md` |
| 看不懂某個詞 | `docs/07_GLOSSARY.md` |

## 目錄

```
trade-desk/
├── docs/          文件（白皮書、架構、教學、維運、路線圖、術語、ADR）
├── shared/        ★ 單一真相：憲法、協定、風控、量尺、Schema、參數、切片與權限設定
├── agents/        15 個 Agent 的工作目錄（人設、手冊、生成的規則切片）
├── skills/        30 個可搬遷技能包
├── router/        Discord Router（系統的心臟）+ 設定
├── engine/        核心程式：唯一碰錢與寫資料的地方（待實作）
├── scripts/       排程任務與工具（4 支已實作）
├── db/            資料庫結構 + 41 個權限視圖
├── backtest/      回測框架（待實作）
├── dashboard/     戰情室（待實作）
├── marketing/     行銷產出
├── data/ logs/    資料倉與日誌（不進 git）
├── tests/         測試
└── dev/           ★ 你的開發工作區 ← 開 Claude Code 請待在這裡
```

每個資料夾都有 `README.md` 說明該放什麼。

## 指揮鏈

**Blacksheep → CEO → 各 Agent**，建置期與營運期都一樣。

你只需要在 Discord 的 `#human-inbox` 跟 CEO 講話；它負責拆解、派工、追蹤、審核，並在需要你決定時發 `HUMAN_DECISION_REQUIRED`。
唯一的例外是最初約 60–90 分鐘的 bootstrap（安裝、建 Bot、啟動 Router）——那段沒辦法委派，因為 CEO 還不存在。細節見 `docs/08_BUILD_PLAN.md` 第一節。

## ⚠️ 兩件最重要的事

1. **專案根目錄刻意沒有 `CLAUDE.md`。** 開發請 `cd dev`，那裡的 `CLAUDE.md` 才是給你的。這樣你的開發 session 與 15 個 Agent 完全互不污染（`docs/adr/ADR-004`）。
2. **改了 `shared/` 任何檔案，必須跑 `python scripts/build_context.py`。** 否則 Agent 會偵測到雜湊不符而停工，Router 也不會啟動——這是設計，不是 bug（`docs/adr/ADR-002`）。

## 狀態

| 部分 | 狀態 |
|---|---|
| 規格（`docs/`、`shared/`、`skills/`、`db/`） | ✅ 完成 |
| Agent 定義（15 個人設 + 手冊 + 切片） | ✅ 完成 |
| Router（`router/discord_router.py`） | ✅ 可執行 |
| 上下文管線（`build_context.py`、`lint_agents.py`、`query_readonly.py`、`init_db.py`） | ✅ 可執行 |
| `engine/`、多數 `scripts/`、`backtest/`、`dashboard/` | ⬜ 待實作，見 `dev/TASKS.md` |
