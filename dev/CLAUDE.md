# TRADE-DESK 開發工作區

> **你（Claude Code）在這裡的身分是「Blacksheep 的開發者助理」，不是任何一個 TRADE-DESK Agent。**
> 這個目錄刻意放在 `agents/` 之外，所以 15 個 Agent 永遠不會載入這份檔案，你也不會載入它們的人設。

## 這裡的定位：備援，不是主要路徑
Blacksheep 的預設建置方式是 **透過 CEO 指揮 FORGE**（見 `../docs/08_BUILD_PLAN.md`）。
`dev/` 是以下五種情況才用：
1. **Bootstrap**：Router 還沒起來，CEO 還不存在（`08_BUILD_PLAN.md` 第一節）
2. **Router 或 FORGE 自己壞了**——修理工壞了不能叫修理工修
3. 同一個 bug FORGE 試了兩次還沒解
4. Claude Pro 額度用完，但 Blacksheep 還想推進
5. 需要看終端機即時輸出除錯

在這裡動手之前，Blacksheep 應該已經跟 CEO 說過一聲（`!pause` 或告知）。完成後要請 CEO 叫 FORGE 補測試與文件，指揮鏈才不會斷。

## 怎麼啟動這個 session（很重要）

```powershell
cd C:\trade_desk\dev
.\dev.cmd
```

`dev.cmd` 做的事是 `claude --add-dir ..`。**`--add-dir ..` 不能省**：
Claude Code 的檔案存取以「啟動目錄」為界，從 `dev\` 啟動的 session 預設讀不到
`..\engine\`、`..\scripts\`、`..\tests\`——而這些正是你要改的東西。
（不要為了省事改成從根目錄啟動：根目錄一旦有 CLAUDE.md，15 個 Agent 全部會載入它，
這是 ADR-004 明確禁止的；lint 第 11 項會擋。）

## 動手之前

```powershell
.\snapshot.cmd 開始修 Router 的排程
```

它就是 `git add -A && git commit`（`--no-verify`，因為這只是存檔點，不是要推出去的東西）。
有這個 commit，任何一次改壞都是 `git diff` 與 `git checkout` 的事，不是靠記性回推。
**大一點的改動請先開分支**：`git switch -c fix/<簡述>`，`/td-check` 全過再併回 `main`。

## Router 正在跑的時候動手（重要）

可以同時開，但要知道兩件事會咬人：

**一、你的未 commit 修改會被 Agent 的守衛還原。**
Router 每呼叫一次 Agent，事後都會跑
`guard_paths.py verify --agent <id> --restore`——它比對受保護檔案的雜湊，
發現「不屬於這個 Agent 權限範圍」的變更就 `git checkout -- <檔案>` 還原。
**你在 `scripts/`、`router/`、`shared/`、`tests/` 的編輯，看起來跟 Agent 的越權寫入一模一樣。**
`git checkout -- <檔案>` 是從 **index** 還原的，所以：
**只要 `git add` 過（`snapshot.cmd` 就會做），還原就是空操作，你的修改不會消失。**
沒存檔就去泡咖啡，回來東西不見了——就是這個機制。
`snapshot.cmd` 同時會重建守衛基準，否則每一次 Agent 呼叫都會誤報一次越權。

**二、設定檔要重啟 Router 才生效。**

| 改了什麼 | 生效方式 |
|---|---|
| `router/agents.yaml`、`router/scheduler.yaml`、`router/.env` | **必須重啟 Router** |
| `router/discord_router.py` | **必須重啟 Router** |
| `shared/` 的任何檔案 | 跑 `build_context.py`，**否則 Agent 會因雜湊不符停工** |
| `agents/*/MANUAL.md`、`PERSONA.md` | 下一次呼叫就生效（Agent 每次都重讀） |
| `scripts/`、`engine/` | 下一次呼叫就生效（都是子程序） |

**三、額度是共用的。** Router 的 45 個排程 + 15 個 Agent 跟你的開發 session
吃同一份 Claude Pro 額度。`@TD-WATCH !budget` 可以看用量；
開發 session 很吃重的時候，先在 Discord 下 `!pause`。

## 結束 session 之前

打 `/td-check`，它會跑完整的驗證鏈。**任一項不過就不算做完。**
這條鏈就是「不會違反白皮書」的保證來源——不是靠記性，是靠這六支程式：

| 驗證 | 它擋住什麼 |
|---|---|
| `build_context.py` | 改了 `shared/` 卻沒重建切片（Agent 會因雜湊不符停工） |
| `verify_docs_claims.py` | 文件宣稱的數字 / 路徑與 repo 不一致 |
| `lint_agents.py` | Agent 定義、職責、權限、Router 的已知地雷（33 項） |
| `verify_isolation.py` | 責任重疊、交接斷線、寫入權與 OWNERSHIP 不符 |
| `pytest` | 行為回歸（118 項，含 Router 的迴圈保護） |
| `guard_paths.py verify` | 受保護檔案被動過 |

**驗證鏈涵蓋不到的是「語意漂移」**——例如你把某個規則改成另一個意思，
但數字與路徑都還對得上。所以還有一條人的規則：
**動到 `shared/` 或 `docs/` 的規則性內容，同一次改動要一併更新文件與 `docs/CHANGELOG.md`。**
沒把握的時候，把改動寫成提案放進 `TASKS.md`，不要直接改。

@NOTES.md
@TASKS.md

## 這個專案是什麼
15 個 AI Agent 組成的量化交易與內容團隊，跑在 Windows 上，用 Claude Pro + Claude Code + 一支 Discord Router。
完整說明：`../docs/00_WHITEPAPER.md`（總綱）、`../docs/01_ARCHITECTURE.md`（架構與理由）。

## 你在這裡做什麼
實作與維護程式：`../engine/`、`../scripts/`、`../router/`、`../dashboard/`、`../backtest/`、`../tests/`。
規格在 `../shared/`；每支程式要做什麼、驗收標準是什麼，看該資料夾的 `README.md`。

## 硬規則（違反會影響真實資金）
1. **不要改 `../shared/RISK_RULES.md`、`../shared/strategy_params.yaml` 的數值。** 那是 Owner 核准事項；要調整先在 `TASKS.md` 記下提案，走白皮書的變更流程。
2. **改完 `../shared/` 的任何檔案，必須跑 `python ../scripts/build_context.py`**，否則 Agent 會因雜湊不符而停工（這是設計，不是 bug）。
3. **改 `../engine/executor.py` 或 `../engine/risk_gate.py` 之前**：先確認系統在 DEMO 模式，或先在 Discord `#human-inbox` 下 `!pause`。Router 每 5 分鐘會呼叫這些程式。
4. **不要在這裡啟動第二個 Router。** 檢查是否已在跑：`Get-Process python | Select-Object CommandLine`。
5. 提交前跑：`python ../scripts/lint_agents.py && python -m pytest ../tests -q`。

## 常用指令
```powershell
cd C:\trade_desk
.\.venv\Scripts\Activate.ps1

python scripts\build_context.py            # 重建 Agent 上下文切片
python scripts\build_context.py --verify   # 驗證切片與 shared/ 一致
python scripts\lint_agents.py              # 檢查 15 個 Agent 定義自洽
python -m pytest tests -q                  # 單元測試
python router\discord_router.py            # 前景啟動 Router（測試用）
sqlite3 data\tradedesk.db < db\002_views.sql   # 重建視圖
```

## 測試單一 Agent（不經 Discord）
```powershell
cd C:\trade_desk\agents\chart
claude -p "請用 PROTOCOL 格式回覆一則 NO_SETUP" --output-format json --model sonnet
```

## 目前進度
建置待辦的**唯一真相**是 `../docs/08_BUILD_PLAN.md`（CEO 從那裡取任務、FORGE 在那裡打勾）。
`TASKS.md` 只是你自己動手時的臨時筆記，不要拿它當主待辦，也不要與 BUILD_PLAN 分岔。
