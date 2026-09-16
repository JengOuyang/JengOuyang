# 02 — 手把手教學：在 Windows 上建立 15 個 AI Agent 並接上 Discord

**環境**：Windows 10/11、24/7 開機、Claude Pro 訂閱、Claude Code 已安裝；**不需要** WSL、Ubuntu、OpenClaw。
**預估時間**：第一次完整設定 4–6 小時（其中 16 隻 Discord Bot 約 1.5 小時、IG 專業帳號與 Meta App 約 1 小時 + 官方審核 2–4 週）。

> 慣例：`PS>` = Windows PowerShell（以系統管理員或一般使用者皆可，會註明）；`claude>` = 在 Claude Code 互動視窗內輸入。
> **[確認]** 來自官方文件；**[建議]** 本專案做法；**[估計]** 需實測。

---

## 目錄
0. 你要蓋的東西（心智模型）
1. Windows 基礎環境
2. Claude Code 安裝、登入、模型確認
3. 部署檔案包到 `C:\trade_desk`
4. Discord 伺服器與 18 個頻道
5. 建立 16 隻 Discord Bot（逐步，含每隻的設定）
6. 把每隻 Bot 連結到對應的 Agent（`router/.env`、`agents.yaml`）
7. 設定每個 Agent（CLAUDE.md、PERSONA、MANUAL、settings.json、Skills）
8. 第一次啟動 Router 與煙霧測試
9. 常駐化（工作排程器 + watchdog）
10. Agent 之間如何即時協作（實際範例）
11. 交易引擎與 Bitget Demo
12. Canva MCP（CREATIVE）
13. Instagram：個人帳號 → 專業帳號 → Meta App → 自動發佈
14. GROWTH 的資料源（IG Insights、Google Trends、Search Console）
15. FORGE 的工作方式（修 bug、加 skill）
16. Token 經濟：怎麼在 Pro 額度內活下去
17. 上線前檢查清單
18. 疑難排解

---

## 0. 你要蓋的東西（心智模型）

- **1 個 Router**（`router/discord_router.py`，Python 常駐）：同時登入 16 隻 Discord Bot。誰被 @，Router 就在那個 Agent 的資料夾裡執行 `claude -p`（LLM 型）或對應的 Python 程式（程式型），再用那隻 Bot 把結果貼回同一個 thread。
- **15 個 Agent = 15 個資料夾**（`agents/<id>/`），每個有自己的 `CLAUDE.md`（Claude Code 自動載入）、`PERSONA.md`、`MANUAL.md`、`.claude/settings.json`（工具白名單）。
- **30 個 Skills**（`skills/<name>/SKILL.md`），安裝到 `~/.claude/skills/` 後所有 Agent 與你其他專案都能用。
- **排程 = Discord 訊息**：到點時 TD-ROUTER 在對應頻道發 `[CRON:job] @Agent 指示`，Agent 的 Bot 收到就處理。所以「所有觸發都有紀錄」。
- **即時**：Discord Gateway 是 WebSocket 推送，< 1 秒到 Router；Router 立刻加 👀；處理中 ⚙️；完成 ✅；失敗 ❌ 並自動 @FORGE。

---

## 1. Windows 基礎環境

1. **電源**：`設定 → 系統 → 電源與電池 → 螢幕與睡眠`：插電時「永不」睡眠。或 `PS> powercfg /change standby-timeout-ac 0`。
2. **時區**：確認為 (UTC+08:00) 台北。
3. **Python 3.12**：https://www.python.org/downloads/windows/ → 安裝時勾選 **Add python.exe to PATH**。驗證：`PS> python --version`。
4. **Git for Windows**：https://git-scm.com/download/win（FORGE/LAB 需要）。驗證：`PS> git --version`。
5. **Node.js LTS**（Claude Code 需要）：https://nodejs.org。驗證：`PS> node --version`。
6. （選用）**Bun**：只有你想額外用官方 Discord Channels plugin 與 CEO 聊天時才需要：`PS> irm bun.sh/install.ps1 | iex` **[確認]**。

---

## 2. Claude Code 安裝、登入、模型確認 **[確認]**

```powershell
PS> irm https://claude.ai/install.ps1 | iex      # 若已安裝可跳過；更新用 claude update
PS> claude --version
PS> mkdir C:\trade_desk-test; cd C:\trade_desk-test
PS> claude
claude> /login                                     # 用你的 Claude Pro 帳號（瀏覽器 OAuth）
claude> /model                                     # 記下可用模型別名：sonnet / opus / haiku（Pro 可用者為準）
claude> /exit
```
測試非互動模式（這就是 Router 會用的方式）：
```powershell
PS> claude -p "回覆 OK 兩個字" --output-format json --model sonnet
```
你應該看到一段 JSON，含 `"result":"OK"`、`"session_id"`、`"usage"`。**這種用法目前計入 Pro 訂閱一般用量**（Anthropic 2026-06-15 暫停了另計額度的方案）**[確認]**。

---

## 3. 部署檔案包

1. 解壓 `trade-desk-v2.zip` 到 `C:\trade_desk`（路徑固定，`watchdog.ps1`、`start.ps1` 都用這個路徑；要改請一併改）。
2. 建立虛擬環境並安裝套件：
```powershell
PS> cd C:\trade_desk
PS> python -m venv .venv
PS> .\.venv\Scripts\Activate.ps1
PS> pip install -r router\requirements.txt
PS> mkdir logs, data, marketing\queue, marketing\longform, marketing\analytics, backtest\reports
```
3. 安裝 Skills 到使用者層（跨專案可用）**[確認：Claude Code 讀 `~/.claude/skills/`]**：
```powershell
PS> mkdir $HOME\.claude\skills -Force
PS> Copy-Item -Recurse -Force C:\trade_desk\skills\* $HOME\.claude\skills\
```
4. 初始化 git（FORGE/LAB 需要）：
```powershell
PS> git init; git add .; git commit -m "trade-desk v2 bootstrap"
```
5. `router\.env.example` 複製為 `router\.env`，之後逐步填入；設定檔案權限只給你：
```powershell
PS> icacls C:\trade_desk\router\.env /inheritance:r /grant:r "$env:USERNAME:(R,W)"
```

---

## 4. Discord 伺服器與 18 個頻道

1. Discord 桌面版 → 左側「+」→ **建立我的伺服器** → 名稱 `TRADE-DESK`（私人）。
2. `使用者設定 → 進階 → 開發者模式` 開啟（之後才能複製 ID）。
3. 右鍵伺服器圖示 → **複製伺服器 ID** → 填入 `router\.env` 的 `GUILD_ID`。
4. 右鍵你的頭像 → **複製使用者 ID** → 填入 `OWNER_USER_ID`，並填入每個 `agents\<id>\USER.md` 的 Owner Discord User ID。
5. 建立 4 個分類與 18 個文字頻道（名稱要完全一致；見 `docs/03_DISCORD_SETUP.md`）：
   - 指揮：`#human-inbox` `#ceo-daily` `#meeting-room` `#tasks`
   - 交易：`#macro` `#market-data` `#analysis` `#risk` `#execution` `#journal` `#backtest`
   - 工程：`#forge`
   - 行銷：`#marketing` `#marketing-review` `#growth`
   - 維運：`#agent-health` `#audit-log` `#alerts`
6. 每個頻道右鍵 → **複製頻道 ID** → 填入 `.env` 的 `CH_*`。
7. 建立角色 `Agents`（顏色自選）與 `Owner`；`#human-inbox` 權限：只有 Owner 與 Agents 可發言。

---

## 5. 建立 16 隻 Discord Bot（逐隻）**[確認：Discord Developer Portal 流程]**

對下表每一列重複 5.1–5.6：

| # | Application 名稱 | Bot 使用者名稱 | 對應 Agent | `.env` 變數 |
|---|---|---|---|---|
| 1 | TD-ROUTER | TD-ROUTER | （系統：發排程訊息）| DISCORD_TOKEN_ROUTER |
| 2 | TD-CEO | TD-CEO | ceo | DISCORD_TOKEN_CEO |
| 3 | TD-MACRO | TD-MACRO | macro | DISCORD_TOKEN_MACRO |
| 4 | TD-FEED | TD-FEED | feed | DISCORD_TOKEN_FEED |
| 5 | TD-LEDGER | TD-LEDGER | ledger | DISCORD_TOKEN_LEDGER |
| 6 | TD-CHART | TD-CHART | chart | DISCORD_TOKEN_CHART |
| 7 | TD-RISK | TD-RISK | risk | DISCORD_TOKEN_RISK |
| 8 | TD-EXEC | TD-EXEC | exec | DISCORD_TOKEN_EXEC |
| 9 | TD-LAB | TD-LAB | lab | DISCORD_TOKEN_LAB |
| 10 | TD-REDTEAM | TD-REDTEAM | redteam | DISCORD_TOKEN_REDTEAM |
| 11 | TD-AUDIT | TD-AUDIT | audit | DISCORD_TOKEN_AUDIT |
| 12 | TD-WATCH | TD-WATCH | watch | DISCORD_TOKEN_WATCH |
| 13 | TD-FORGE | TD-FORGE | forge | DISCORD_TOKEN_FORGE |
| 14 | TD-CMO | TD-CMO | cmo | DISCORD_TOKEN_CMO |
| 15 | TD-CREATIVE | TD-CREATIVE | creative | DISCORD_TOKEN_CREATIVE |
| 16 | TD-GROWTH | TD-GROWTH | growth | DISCORD_TOKEN_GROWTH |

### 5.1 建立 Application
https://discord.com/developers/applications → **New Application** → Name 填表中名稱 → Create。
（建議上傳頭像：用 Canva 做 16 個同風格的圓形圖示，寫上代號，日後在頻道裡一眼分辨。）

### 5.2 建立 Bot 與 Token
左側 **Bot** → Username 改為表中名稱 → **Reset Token** → Yes → **Copy**。
**立刻**貼到 `router\.env` 對應的變數（Token 只顯示一次；遺失就再 Reset）。

### 5.3 Privileged Gateway Intents（每隻都要）
同頁往下：
- ✅ **Message Content Intent**（必要，否則 Bot 讀不到訊息內容）
- ✅ **Server Members Intent**（Router 需要解析成員／@mention）
- ⬜ Presence Intent（不用）
按 **Save Changes**。

### 5.4 關閉「Public Bot」——**順序不能顛倒**

直接去關 Public Bot 會被擋下，錯誤訊息是：

> 私人應用程式不得使用預設授權連結。請確認安裝分頁中的預設授權連結設定為「無」。

原因：Discord 不允許「私人應用程式」同時保有一條官方產生的安裝連結。
所以要先把那條連結拿掉，才關得掉 Public Bot：

1. 左側 **Installation（安裝）** → **Install Link（安裝連結）** → 選 **None（無）** → **Save Changes**
2. 回到左側 **Bot** → **Authorization Flow** → 關閉 **Public Bot** → **Save Changes**

**如果第 1 步也存不了**，訊息會提到 discoverable / 探索：代表這個應用程式開了 App Discovery。
先到左側 **App Discovery** 頁最下方按 **Disable Discovery**，再回頭做第 1 步。
（一般新建的應用程式不會有這個問題。）

> Install Link 設成 None 只是拿掉「Discord 幫你產生的那條安裝連結」，
> 不影響你自己用 OAuth2 URL Generator 產生邀請連結——下一步就是做這個。

### 5.5 產生邀請連結並加入伺服器

左側 **OAuth2 → URL Generator**。

**Scopes 的清單很長**（identify、email、guilds、rpc.*、applications.* …二十幾個），
那是 Discord 的完整清單，每個應用程式都一樣。**你只勾一個：`bot`**，其餘全部不勾。

> 不需要 `applications.commands`——本專案不用斜線指令，
> Owner 指令走 `!approve` 這種文字訊息，Agent 靠 @mention 觸發。

勾了 `bot` 之後，下方會冒出 **Bot Permissions**，勾這九個：

`View Channels`、`Send Messages`、`Send Messages in Threads`、`Create Public Threads`、
`Read Message History`、`Attach Files`、`Embed Links`、`Add Reactions`、`Manage Threads`

複製最下方 **Generated URL** → 瀏覽器開啟 → 選 `TRADE-DESK` 伺服器 → 授權。
回到 Discord 應看到該 Bot 出現在成員列表（離線，正常）。

### 5.6 記錄 Application ID（可選）
**General Information → Application ID**：Router 啟動後會自動取得，不需手填；但建議記在 `docs/03_DISCORD_SETUP.md` 方便對照。

> 做完 16 次後，`router\.env` 的 16 個 `DISCORD_TOKEN_*` 都應有值。**Token = 該 Bot 的密碼，不要貼到任何頻道。**

---

## 6. 把每隻 Bot 連結到對應的 Agent

連結關係在 `router\agents.yaml`：每個 Agent 的 `token_env` 指向 `.env` 的變數名。預設已對好，你只需要確認：

```yaml
agents:
  ceo:
    name: TD-CEO
    kind: llm                     # llm = 用 claude -p；program = 執行程式；router = 只發排程
    token_env: DISCORD_TOKEN_CEO  # ← 對應 .env
    model: sonnet                 # 預設模型；排程可用 model: opus 覆寫
    max_turns: 15
    allowed_tools: [...]          # 傳給 claude -p --allowedTools
    owner_commands: ["!status", "!task", "!approve", "!unlock"]
```

要新增第 16 個 Agent（例如「TAX」報稅助理）：
1. 建 Discord Bot（第 5 步）→ `.env` 加 `DISCORD_TOKEN_TAX`。
2. `agents.yaml` 加一段 `tax:`。
3. `agents\tax\` 建 `CLAUDE.md`、`PERSONA.md`、`MANUAL.md`、`USER.md`、`.claude\settings.json`（複製 `agents\audit\` 改）。
4. `scheduler.yaml` 加排程（若需要）。
5. 重啟 Router（或請 FORGE 做這整件事：在 `#forge` 打 `@TD-FORGE 請建立 TAX Agent，職責：…`）。

---

## 7. 設定每個 Agent

每個 `agents\<id>\` 已包含：

| 檔案 | 作用 | 你要改嗎 |
|---|---|---|
| `CLAUDE.md` | Claude Code 啟動自動載入；用 `@PERSONA.md`、`@MANUAL.md`、`@../../shared/...` 引入 **[確認：CLAUDE.md 支援 @import]** | 不用 |
| `PERSONA.md` | 身分、性格、決策原則、禁忌、升級路徑、共同信條 | 可依喜好微調語氣 |
| `MANUAL.md` | 職責、觸發、輸入輸出、Skills、工具白名單、額度、KPI、模板、完成定義 | 需求變更時改（或請 FORGE 改） |
| `.context/` | **生成物**：憲法 + 由 `shared/` 切出的角色規則 + MANIFEST.json | 不要手改；改 `shared/` 後跑 `build_context.py` |
| `USER.md` | 你的 Discord ID、偏好、品牌 | **必填** |
| `.claude\settings.json` | 該 Agent 的 `permissions.allow/deny`、預設 model | 模型 ID 以 `/model` 為準 |
| `outbox\` | Agent 要交付的檔案放這裡，Router 會上傳到 Discord | 不用 |

每個 Agent 的 `.context/` 只含它該知道的條款——例如 CHART 只有「提案要件」（A 節），看不到 Gate 門檻（G 節）。這是刻意的，理由見 `docs/adr/ADR-002`。

**驗證單一 Agent 是否正常**（不經 Discord）：
```powershell
PS> cd C:\trade_desk\agents\ceo
PS> claude -p "請用 PROTOCOL 格式回覆一則 TASK_ACK，task_id T-TEST-001" --output-format json --model sonnet
```
看 `result` 是否為「一行摘要 + JSON code block」。15 個 Agent 各測一次（程式型的 feed/ledger/exec 也可測，它們的 CLAUDE.md 會讓 LLM 回答狀態說明）。

---

## 8. 第一次啟動 Router 與煙霧測試

```powershell
PS> cd C:\trade_desk\router
PS> ..\.venv\Scripts\Activate.ps1
PS> python discord_router.py
```
Router 會先跑 **preflight**（驗證 15 個 `.context/` 與 `shared/` 一致、Agent 定義自洽），不通過就不啟動並在日誌說明原因。通過後你應該在 `logs\router.log` 看到 16 行 `bot ready: ... `，Discord 成員列表中 16 隻 Bot 上線。

**測試 1（Owner → Agent）**：在 `#human-inbox` 打
`@TD-CEO !status`
→ 訊息出現 👀 → ⚙️ → CEO 開 thread 回覆 → ✅。

**測試 2（Agent → Agent 即時交接）**：在 `#tasks` 打
`@TD-CEO 請派一個測試任務給 MACRO：回覆今天台北日期與一個總經觀察，驗收標準：附一個來源 URL`
→ CEO 發 TASK_ASSIGN 並 @TD-MACRO → MACRO 的 Bot 收到（👀 在數秒內出現）→ 回 TASK_ACK → 做完 TASK_DONE → CEO REVIEW_RESULT。

**測試 3（排程）**：把 `scheduler.yaml` 任一 job 的 cron 暫改為 2 分鐘後 → 重啟 Router → 觀察 TD-ROUTER 在對應頻道發 `[CRON:...]` 訊息並被處理。

**測試 4（失敗路徑）**：在 `#execution` 打 `@TD-EXEC 你好`（engine/executor.py 尚未實作）→ 應看到 ❌ 並在 `#forge` 出現自動 BUG_REPORT @TD-FORGE → FORGE 會回覆分析（這也是你第一次看 FORGE 工作）。

---

## 9. 常駐化 **[建議]**

1. **登入時啟動 Router**：`工作排程器 → 建立工作`：
   - 一般：名稱 `TradeDesk Router`；「只在使用者登入時執行」；勾「以最高權限執行」不需要。
   - 觸發程序：登入時。
   - 動作：程式 `C:\trade_desk\.venv\Scripts\python.exe`，引數 `C:\trade_desk\router\discord_router.py`，起始於 `C:\trade_desk\router`。
   - 設定：勾「如果工作失敗，重新啟動間隔 1 分鐘，最多 999 次」；取消「如果工作執行超過 3 天就停止」。
2. **Watchdog**：再建一個工作 `TradeDesk Watchdog`，觸發「每 5 分鐘（無限期）」，動作 `powershell.exe -ExecutionPolicy Bypass -File C:\trade_desk\router\watchdog.ps1`。
3. **自動登入**：Router 需要使用者工作階段（Claude Code 的 OAuth token 在你的使用者設定檔）。若電腦重開機後無人登入，Router 不會啟動。可用 `netplwiz` 設定自動登入（了解安全風險後再做），或改成「不論使用者登入與否都執行」並確認 `claude` 在該情境下能讀到登入狀態（需實測 **[估計]**）。
4. **Claude 登入到期**：Claude Code 的 OAuth 偶爾需要重新登入。WATCH 的 `usage.py --check` 會偵測 `claude -p` 回傳認證錯誤並在 `#alerts` @你；此時開 PowerShell 跑 `claude` → `/login` 即可。

---

## 10. Agent 之間如何即時協作（實際範例）

### 10.1 每小時交易循環
```
:01 TD-ROUTER 在 #market-data 發 [CRON:feed-collect] @TD-FEED → FEED 程式採集 → ✅
:05 TD-ROUTER 先跑 prefilter_1h.py；若輸出 SKIP 就什麼都不發（省額度）；
    否則發 [CRON:chart-1h] @TD-CHART（附候選 JSON）→ CHART 用 sonnet 跑決策樹
    → 回覆「BTCUSDT LONG OB_RETEST RR 2.4」+ TRADE_PLAN JSON，並 @TD-RISK（confidence≥0.7 也 @TD-REDTEAM）
    → RISK 的 Bot 秒級收到 → on_mention 程式 risk_gate.py --from-discord 解析 TRADE_PLAN → 執行 Gate
    → 回覆 RISK_DECISION 並 @TD-EXEC（approved）
    → EXEC 程式下單、掛 SL/TP → ORDER_EVENT
    → 平倉後 EXEC 在 #execution 發 POSITION_CLOSED @TD-AUDIT → AUDIT 15 分鐘內 TRADE_REVIEW
```
全部在 Discord 上可見，每一步有 👀/⚙️/✅。

### 10.2 你下需求
`#human-inbox`：`@TD-CEO !task 評估把 TP1 從 2R 改成 1.5R`
→ CEO 立項 T-…-001，`#tasks` @TD-LAB → LAB 回測（可能跑 20–40 分鐘，⚙️ 持續）→ `#backtest` BACKTEST_REPORT @TD-REDTEAM → REDTEAM 盲審 → @TD-RISK 簽核 → CEO 在 `#ceo-daily` 發 HUMAN_DECISION_REQUIRED @你 → 你 `!approve CHG-…` → WATCH 程式更新 `strategy_params.yaml` 並寫 `config_versions` → Router 熱重載。

### 10.3 會議
週日 21:00 `[CRON:ceo-weekly-meeting]` → CEO 在 `#meeting-room` 開 thread `[MTG] 2026-09-13 週會`，逐一 @TD-MACRO、@TD-CHART、@TD-RISK、@TD-AUDIT、@TD-CMO 回答各自 agenda（每個都在同一 thread，因為 Router 會把後續 @ 的回覆貼到同 thread）→ CEO 收斂 MEETING_MINUTES。你隨時可以在 thread 內插話，Agent 會把你的話當 Owner 指示。

### 10.4 內容發佈
15:00 `[CRON:creative-daily]` → CREATIVE 讀 MACRO_BRIEF + HTF_CONTEXT → Canva MCP 產圖 → 圖存 `marketing/queue/...` 並放一份到 `outbox/`（Router 上傳）→ `#marketing-review` 出現預覽 + PUBLISH_REQUEST @你 → 你回 `@TD-CREATIVE !publish c_20260908_macro` → `scripts/publisher.py` 發佈 → PUBLISHED @TD-GROWTH。

### 10.5 迴圈與額度保護
- 每則訊息帶 `hop`，≥ 6 停止並 @CEO。
- 每 Agent 每小時 LLM 呼叫上限（`strategy_params.yaml: llm_budget`）；超過 → ⏳ 延後 15 分鐘並在 `#agent-health` 說明。
- 同時最多 3 個 `claude -p`。

---

## 11. 交易引擎與 Bitget Demo

檔案包提供的是**規格**（`shared/`、`skills/`）；`engine/`、`scripts/` 由 FORGE 與 LAB 在你監督下依規格實作（路線圖第 2–4 週）。啟動方式：在 `#forge` 打
`@TD-FORGE 請依 skills/market-data-collection 與 shared/DATA_SCHEMA.md 實作 scripts/collect_hourly.py 與 engine/ingest_server.py（T1 標的），含 pytest`。

Bitget 準備 **[確認／建議]**：
1. Bitget → 帳戶 → API 管理 → 建立 API：權限只勾「合約：讀取、交易」，**不勾提幣**；IP 白名單填你家的對外 IP（`PS> (Invoke-WebRequest ifconfig.me).Content`；若浮動 IP，考慮固定 IP 方案或每次變動時更新）。
2. Bitget 開啟 **模擬交易（Demo Trading）**；程式以 ccxt `enable_demo_trading(True)` 連線（送 `PAPTRADING=1`）。
3. `.env`：`BITGET_DEMO=1`；`strategy_params.yaml: mode: DEMO`。
4. 幣股／黃金永續與 BTC 同一個 `productType=USDT-FUTURES`，用 `GET /api/v2/mix/market/contracts` 取得每檔的面值、最小量、精度 **[確認]**。

---

## 12. Canva MCP（CREATIVE）**[確認：Canva MCP 文件]**

1. 在 Claude Code 互動視窗把 Canva 加為 MCP（使用者層，之後 `claude -p` 也能用）：
```powershell
PS> claude mcp add --transport http --scope user canva https://mcp.canva.com/mcp
PS> cd C:\trade_desk\agents\creative; claude
claude> /mcp            # 選 canva → Authenticate → 瀏覽器登入 Canva 授權
claude> 用 canva 列出我的品牌模板
claude> /exit
```
2. 在 Canva 建 4 個品牌模板：`TD-Daily-Macro`、`TD-Daily-Chart`、`TD-Edu`、`TD-Weekly`（1080×1350；固定品牌標、日期、底部聲明的文字框）。品牌模板／autofill 屬 Canva Enterprise 功能 **[確認]**；免費／Pro 方案改用「設計副本 + edit-design 改文字」流程，CREATIVE 的 `canva-content` skill 已寫兩種做法。
3. `router/agents.yaml` 的 `creative.mcp_config: router/mcp_canva.json` 讓 `claude -p` 帶入 Canva MCP；OAuth 已在第 1 步完成。

---

## 13. Instagram：個人帳號 → 專業帳號 → Meta App → 自動發佈 **[確認：Meta 內容發佈 API 要求]**

### 13.1 轉為專業帳號並綁定 Facebook 粉絲專頁
1. IG App → 個人檔案 → 選單 → 設定 → 帳號類型與工具 → **切換為專業帳號** → 選「創作者」或「商家」（皆可用 API）。
2. 建立 Facebook 粉絲專頁（若無）：facebook.com/pages/create → 名稱同品牌。
3. IG 設定 → 商業工具與控制項 → **連結 Facebook 粉絲專頁**。

### 13.2 Meta 開發者 App
1. https://developers.facebook.com → 我的應用程式 → **建立應用程式** → 用途「其他」→ 類型「商家」→ 名稱 `TRADE-DESK Publisher`。
2. 新增產品：**Instagram**（Instagram API with Instagram Login 或 with Facebook Login 皆可；本教學以 Facebook Login 版為例）。
3. 設定 → 基本資料：記下 **App ID / App Secret** → `.env` 的 `META_APP_ID/META_APP_SECRET`。

### 13.3 取得長期 Token（開發階段可先用自己的帳號，不需審核）
1. **Graph API Explorer**（developers.facebook.com/tools/explorer）→ 選你的 App → 權限勾：`instagram_basic`、`instagram_content_publish`、`instagram_manage_insights`、`pages_show_list`、`pages_read_engagement`、`business_management` → Generate Access Token（登入授權）。
2. 換長期 token（60 天）：
`GET https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`
3. 取得 IG User ID：`GET /me/accounts` → 找粉專 id → `GET /{page-id}?fields=instagram_business_account` → 記下 `IG_USER_ID`。
4. `.env`：`IG_USER_ID`、`IG_LONG_LIVED_TOKEN`。GROWTH 會在到期前 7 天提醒你更新（或由 FORGE 寫自動刷新）。

### 13.4 圖片公開網址
Meta 只接受 **公開 URL** 的 JPEG **[確認]**。做法（擇一）：
- GitHub Pages：建 `trade-desk-media` 公開 repo，`publisher.py` 把圖 commit 進去，URL = `https://<user>.github.io/trade-desk-media/<file>.jpg`。
- Cloudflare R2 + 公開 bucket（免費額度足夠）。
`.env`：`IMAGE_HOST_BASE_URL`。

### 13.5 發佈流程（`scripts/publisher.py` 規格）
1. 讀 `marketing/queue/<date>/<content_id>/meta.json`；確認 `status=APPROVED`（由 `!publish` 設定）。
2. 上傳圖片到公開網址。
3. `POST https://graph.facebook.com/v21.0/{IG_USER_ID}/media` `image_url=...&caption=...`（輪播：每張先建 `is_carousel_item=true` 的容器，再建 `media_type=CAROUSEL&children=...`）。
4. `POST /{IG_USER_ID}/media_publish` `creation_id=<container-id>`。
5. 寫 `content` 表（ig_media_id、permalink）→ `#marketing-review` 發 PUBLISHED @TD-GROWTH。
限制：每帳號每 24 小時最多 100 篇 API 發佈 **[確認]**（本專案每日 ≤ 2）。

### 13.6 App 審核（要讓 App 正式上線或給他人用時才需要）
開發模式下，**App 的管理員／開發者／測試人員角色帳號**可直接使用上述權限，不需審核；你自己的 IG 綁自己的 App 即屬此情況 **[確認：Meta 開發模式規則，實作時再核對]**。若日後要切到「上線模式」，需為 `instagram_content_publish` 等權限提交審核（含操作影片），約 2–4 週 **[確認：第三方整理]**。

---

## 14. GROWTH 的資料源

| 資料 | 取得方式 | 需要 |
|---|---|---|
| IG 帳號／貼文 Insights | Graph API `/{IG_USER_ID}/insights?metric=reach,impressions,profile_views,follower_count&period=day`、`/{media-id}/insights?metric=reach,saved,shares,likes,comments` | `instagram_manage_insights` |
| 受眾輪廓 | `/{IG_USER_ID}/insights?metric=audience_city,audience_gender_age&period=lifetime`（需 ≥ 100 追蹤者） | 同上 |
| Google Trends | `pytrends`（非官方，免費） | 無 |
| Search Console | Google Cloud 專案 + OAuth；`scripts/gsc.py` | 有網站才需要 |
| GA4 | GA4 Data API | 有網站才需要 |
| 留言／私訊 | Graph API comments；私訊需 `instagram_manage_messages` 與額外審核 | 第二階段 |

---

## 15. FORGE 的工作方式

- **回報 bug**：任何頻道 `@TD-FORGE` + 描述，或等 Router 的自動 ❌ BUG_REPORT。
- **要新能力**：`@TD-FORGE SKILL_REQUEST：讓 CHART 能讀 CME 期貨缺口；驗收：levels.py 輸出 cme_gaps[]`。
- FORGE 在 `agents/forge/` 以 `git worktree` 開分支工作，跑 `pytest`，回 FIX_PROPOSAL；涉及 EXEC/RISK/LEDGER 的改動需 `@TD-REDTEAM` 審 + 你 `!approve`。
- 每月 2 日 23:50 `scripts/lint_agents.py`：檢查每個 Agent 的 MANUAL 提到的 skills 是否存在、`agents.yaml` 的 allowed_tools 是否與 `settings.json` 一致、msg_type 是否在 PROTOCOL 內。

---

## 16. Token 經濟：在 Pro 額度內活下去 **[估計]**

- Pro = 5 小時滾動窗 + 週上限，`claude -p` 與互動共用。
- 本設計每日約 15–40 次 `claude -p`，多數 sonnet/haiku、輸入短（資料由程式先算好）、輸出短（JSON）。
- 省額度開關（都已內建）：`precheck`（prefilter、事件日曆、任務預判）、`model: haiku` 的例行任務、`global_parallel: 3`、`per_agent_hourly_calls`、額度低時延後 cmo/growth/lab。
- 何時升級 Max 5x：當 `#agent-health` 每天出現 ⏳ 延後、或你想開 T2–T4、或每日內容 > 2 篇。升級後不用改任何設定。
- 可額外省：把 REDTEAM 的每日 HTF 盲審改為每週 3 次；CEO 任務掃描改每小時。

---

## 17. 上線前檢查清單

- [ ] 16 隻 Bot 上線；`#human-inbox` `@TD-CEO !status` 有 ✅
- [ ] 測試 2（CEO → MACRO 交接）在 60 秒內看到 MACRO 的 👀
- [ ] `USER.md` 都填了 Owner ID；`!flatten` 在 DEMO 測試成功
- [ ] `scheduler.yaml` 全部 job 至少手動觸發過一次
- [ ] 工作排程器兩個工作（Router、Watchdog）建立並測試重開機
- [ ] 資料倉 hash chain 驗證程式跑過；`#audit-log` 有 AUDIT_ANCHOR
- [ ] Bitget API 無提幣、綁 IP；`mode: DEMO`
- [ ] Canva MCP 在 `claude -p` 下可用（CREATIVE 產出過一張圖）
- [ ] IG 專業帳號 + 粉專 + 長期 token；`publisher.py --status` 正常
- [ ] 至少一份 BACKTEST_REPORT 通過；REDTEAM 無 DISAGREE
- [ ] 模擬盤連續 4 週；CEO 每日匯報穩定
- [ ] 你已閱讀並接受 CONSTITUTION §三「人類保留權限」

---

## 18. 疑難排解

| 症狀 | 檢查 |
|---|---|
| Bot 上線但不回應 @ | Message Content Intent 是否開；`.env` 的 GUILD_ID 是否正確；`logs\router.log` |
| 👀 出現但一直 ⚙️ | `claude -p` 在跑（LAB/FORGE 可到 40 分鐘）；或 Claude 登入過期（跑 `claude` → `/login`） |
| ❌ 且 #forge 出現 BUG_REPORT | 正常路徑；看 FORGE 的分析 |
| 回覆被截斷 | Router 已分段；若 JSON 壞掉，是 Agent 輸出超過 `max_turns` 被中止，調高或縮小任務 |
| 排程沒觸發 | Router 是否在跑；`scheduler.yaml` cron 語法；時區 |
| Canva 工具不存在 | `claude mcp list`；重新 `/mcp` 授權；`mcp_config` 路徑 |
| IG 發佈 400 | 圖片 URL 是否公開可讀、JPEG、比例 4:5–1.91:1；token 是否過期 |
| 額度用完 | `#agent-health` 的 ⏳；等待窗口重置；考慮 Max |

---

## 參考來源
- Claude Code 安裝／CLI／`-p` 旗標：https://code.claude.com/docs/en/cli-reference
- Claude Code Channels（Discord plugin，選用）：https://code.claude.com/docs/en/channels
- Claude Code Subagents 與 skills 預載：https://code.claude.com/docs/en/sub-agents
- `claude -p` 用量政策（2026-06-15 暫停另計）：https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan
- Discord Developer Portal：https://discord.com/developers/applications
- Canva MCP：https://www.canva.dev/docs/mcp/
- Instagram 內容發佈 API 流程：https://postproxy.dev/blog/post-to-instagram-via-api/
- Bitget 合約列表 API：https://www.bitget.com/api-doc/contract/market/Get-All-Symbols-Contracts
- ccxt Bitget：https://docs.ccxt.com/exchanges/bitget
