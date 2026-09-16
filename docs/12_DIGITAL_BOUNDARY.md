# 12　數位邊界：15 個 Agent 怎麼互不干擾

> 這份文件回答一個問題：**「絕對無法更動不屬於自己的東西」這句話，在這個系統裡到底成立到哪一步？**
> 先給答案，分兩種環境：
> **原生 Windows（Blacksheep 目前的設定）**——成立到「偵測得到並自動還原」，擋不住。
> **WSL2 / Linux / macOS**——對 Bash 子程序成立到「做不到」；對 Read/Write/Edit 內建工具仍是「工具層拒絕 + 偵測還原」。
> 下面說明為什麼、外面的人怎麼做、我們選了什麼、以及這個取捨的真實成本。

---

## 一、先承認一件事：工具層授權不是沙箱

`agents/<id>/.claude/settings.json` 裡的 `permissions.allow` / `deny` 是**工具層**授權。
Claude Code 在呼叫 Read / Write / Edit / Bash 之前比對規則，不符合就拒絕。

它擋不住的是：**已經在跑的子程序**。

Anthropic 自己的文件寫得很直白——權限系統「是一道權限閘門，不是沙箱；
除了對 `rm`/`rmdir` 的關鍵路徑檢查與受保護路徑清單之外，它不會從指令的目標路徑或效果推斷危不危險」
（[Securely deploying AI agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment)）。

具體到本專案，`scripts/verify_isolation.py` 一直誠實列出兩條逃逸路徑：

| Agent | 有寫入權 | 有執行權 | 後果 |
|---|---|---|---|
| FORGE | `Write(worktree/**)` | `Bash(python worktree/*)` | 可以在 worktree 寫一支 .py，再執行它，那支程式想寫哪就寫哪 |
| LAB | `Write(../../backtest/**)` | `Bash(python ../../backtest/*)` | 同上 |

這不是設計失誤——FORGE 要修程式、LAB 要跑回測，本來就必須同時有這兩件事。
**問題不在權限給太多，在於工具層根本不是正確的執行點。**

---

## 二、外面的人怎麼處理（網路上的做法）

我查了四類做法，各自的取捨如下。

### 1. OS 層沙箱（Anthropic 官方路線）

Anthropic 2025 年底把沙箱做進 Claude Code：Linux/WSL2 用
[bubblewrap](https://github.com/containers/bubblewrap)、macOS 用 Seatbelt，
限制**套用到 Bash 指令與它所有的子程序**。他們的工程文章說這樣做讓權限提示減少 84%，
並且明確主張兩道邊界缺一不可：「網路隔離防止 SSH 金鑰之類的檔案被外傳；
檔案系統隔離防止逃出沙箱」（[Claude Code sandboxing](https://anthropic.com/engineering/claude-code-sandboxing)）。

他們也指出一個反直覺的點：**一直跳權限提示反而更不安全**，因為會養出「approval fatigue」，
人開始不看內容就按同意。這對本專案特別relevant——15 個 Agent 每天跑 45 個排程任務，
任何需要人工按同意的設計都會在第三天崩潰。

- 優點：規則就寫在 settings.json 裡，沒有容器、沒有映像檔、開銷極低
- 代價：**原生 Windows 不支援**（官方文件「Platform and tool compatibility」一節明列
  「WSL1 and native Windows are not supported」），必須跑在 WSL2 裡
- 限制：預設不做 TLS 檢查，網域允許清單靠 client 端提供的 hostname 判斷，
  理論上可被 domain fronting 繞過；Read/Write/Edit 這些內建工具走權限系統，不經過沙箱

### 2. 容器 / devcontainer

社群主流做法是把每個 agent 丟進 Docker，用 `--cap-drop ALL`、`--read-only`、
`--network none` + Unix socket proxy 來收斂。官方文件給了完整的 hardened 範例。

- 優點：隔離強度可調，也順便隔離 runtime（下面第 4 點會講為什麼這重要）
- 代價：Windows 上要跑 Docker Desktop，15 個 agent 15 個容器，
  Router 要管容器生命週期；對單人專案是明顯的過度工程

### 3. 獨立 OS 帳號 + 檔案 ACL

Homebrew 的 Mike McQuaid 在
[Sandboxes and Worktrees](https://mikemcquaid.com/sandboxed-agent-worktrees-my-coding-and-ai-setup-in-2026/)
描述他的做法：用 `sandvault` 建一個**權限受限的獨立使用者帳號**跑 agent，
倉庫放在 `/Users/Shared/` 下讓兩個身分都讀得到。他的結論跟 Anthropic 一致——
「權限對話框是生產力殺手，OS 沙箱才是解法」。

在 Windows 上的對應做法是：每個 Agent 一個本機使用者帳號 + NTFS ACL，Router 用 `runas` 啟動。
這是**真正的預防**，但 Router 要處理 15 組憑證、檔案擁有權會變得難以維護、
而且 Claude Code 的 session 檔、快取都要各自一份。本專案評估後不採用（見第四節）。

### 4. git worktree —— 必要但不充分

多 agent 並行開發的標準做法是每個 agent 一個 worktree。本專案的 FORGE 就是這樣設計的。
但要注意 worktree 解決的是**程式碼衝突**，不是隔離：

> 「worktree 共用 runtime 基礎設施，卻看起來像是隔離的環境。」
> ——[Git Worktrees Need Runtime Isolation](https://www.penligent.ai/hackinglabs/git-worktrees-need-runtime-isolation-for-parallel-ai-agent-development/)

它列出的失效模式（連接埠衝突、共用資料庫造成跨分支污染、`.env` 與 host 掛載路徑
在並行執行之間無聲傳播、測試失敗訊號變得無法歸因）對本專案**部分適用**：
Router 已經把每個 Agent 的並行度限制為 1，所以沒有連接埠競爭；
但「共用資料庫」這條完全適用——15 個 Agent 讀同一個 `data/tradedesk.db`。
我們的對策不是隔離資料庫，而是**視圖層授權 + `PRAGMA query_only=1` 唯讀連線**（見 `shared/view_grants.yaml`）。

---

## 三、本專案採用的四層邊界

由外而內，每一層擋的東西不同。**沒有任何一層是充分的，這就是為什麼要四層。**
（原生 Windows 只有 L1–L3；L0 的規則仍然生成並驗證，搬進 WSL2 就立刻生效，不需要改任何東西。）

```
L0  OS 層沙箱      bubblewrap / Seatbelt        擋：Bash 指令與其所有子程序
     ↑ 由 scripts/sync_sandbox.py 從 OWNERSHIP.yaml 生成，lint 第 21 項驗證
     ↑ 原生 Windows 不存在這一層（TD_REQUIRE_SANDBOX=0）

L1  工具層授權     settings.json allow/deny     擋：Read / Write / Edit / Bash 呼叫本身
     ↑ lint 第 14 項強制 deny 基線；verify_isolation.py 第 4 項比對 OWNERSHIP

L2  執行層沙箱     git worktree + merge_fix.py  擋：FORGE 的變更未經審核進入活動樹
     ↑ FORGE 無 merge / push 權；合併需 REDTEAM 覆核 + Blacksheep !approve

L3  偵測層         guard_paths.py 雜湊比對       擋：前三層都漏掉的情況（事後）
     ↑ Router 每次呼叫 Agent 前後各驗一次，未授權變更 → git checkout 還原 + HALT + @Blacksheep
```

### L0 具體長什麼樣

`scripts/sync_sandbox.py` 把 `shared/OWNERSHIP.yaml` 的 `writable_paths` 翻譯成沙箱規則。
以 LAB 為例（它擁有 `backtest/**`）：

```json
"sandbox": {
  "enabled": true,
  "filesystem": {
    "allowWrite": ["../../backtest", "./outbox"],
    "denyWrite": ["../../shared", "../../engine", "../../router", "../../scripts",
                  "../../db", "../../docs", "../../tests", "../../data",
                  "../../agents/chart", "../../agents/risk", "... 其餘 12 個 Agent ...",
                  "./.context", "./MANUAL.md", "./PERSONA.md", "./USER.md", "./CLAUDE.md"],
    "denyRead":  ["../../router/.env", "... 其他 Agent 的 USER.md 與身分檔 ..."]
  },
  "network": { "allowedDomains": [] },
  "credentials": {
    "files":   [{"path": "~/.ssh", "mode": "deny"}, {"path": "../../router/.env", "mode": "deny"}],
    "envVars": [{"name": "BITGET_API_SECRET", "mode": "deny"}, ...]
  }
}
```

三個重點：

1. **`denyRead` 鏡射 L1 的 deny。** CHART 在工具層被 deny `Read(../../shared/RISK_RULES.md)`
   （Goodhart 防護：它不能看到 Gate 門檻），但在 L0 之前它可以用 Bash `cat` 讀到。
   `sync_sandbox.py` 會把每一條 `Read(...)` deny 自動翻成 `denyRead`，這道防線才不是紙做的。
2. **兩個刻意的例外。** `data/` 不進 `denyRead`——被授權的查詢路徑 `scripts/query_readonly.py`
   是 Bash 子程序，它必須開得了 `data/*.db`（寫入仍然全面禁止）。
   自己的身分檔不進 `denyRead`——工具層的 `Read(../../agents/*/PERSONA.md)`
   從自己目錄看是相對路徑擋不到自己，沙箱比對的是真實路徑，不排除就會把 Agent 鎖在門外。
3. **`allowedDomains: []`。** LLM Agent 的 Bash 只跑本機查詢腳本，不需要任何外網。
   採集與下單是 program 型 Agent（`engine/`），由 Router 直接執行，不經過這裡。

### Router 補上三個只有 CLI 能開的開關

`strictAllowlist`、`allowUnsandboxedCommands`、`failIfUnavailable`
這三項 Claude Code **只接受**來自使用者設定、managed 設定或 CLI `--settings`，
放在專案的 `.claude/settings.json` 會被忽略（這是刻意的：避免簽出的專案自己放寬限制）。
所以 `router/discord_router.py` 在每次呼叫時帶上：

```python
REQUIRE_SANDBOX = os.environ.get("TD_REQUIRE_SANDBOX", "0") == "1"

SESSION_HARDENING = {"sandbox": {"enabled": True,
                                 "failIfUnavailable": REQUIRE_SANDBOX,
                                 "allowUnsandboxedCommands": not REQUIRE_SANDBOX,
                                 "network": {"strictAllowlist": True}}}
```

`TD_REQUIRE_SANDBOX` 在 `router/.env`，預設 `0`（原生 Windows）。

設 `1` 時 `failIfUnavailable` 為真：**沙箱起不來就讓呼叫失敗**。
Claude Code 的預設行為是「沙箱不可用時印個警告然後不沙箱地跑」——
那對這個系統是最糟的失效模式：你以為有保護，其實沒有。
所以設 `0` 的時候，改由 Router 的 `preflight()` 在每次啟動大聲印出目前的隔離層級。

---

## 四、對 Blacksheep 的具體結論

### 1. Blacksheep 的選擇：Windows 原生（三層），WSL2 是可選升級（四層）

你選擇跑原生 Windows，這是專案的預設設定（`TD_REQUIRE_SANDBOX=0`）。
說清楚你拿到什麼、放棄什麼：

| | Windows 原生（你的設定） | WSL2 |
|---|---|---|
| L0 OS 沙箱 | ❌ | ✅ |
| L1 / L2 / L3 | ✅ | ✅ |
| FORGE / LAB 的逃逸路徑 | **擋不住，但 30 秒內偵測 + 自動 `git checkout` 還原 + HALT + @你** | 擋得住 |
| `Bash(cat router/.env)` | 工具層 deny 擋得住 `Read`，**擋不住 Bash**（[claude-code#46740](https://github.com/anthropics/claude-code/issues/46740)） | 沙箱 `denyRead` 擋得住 |
| 額外安裝 | 無 | 一次，約 10 分鐘 |

**這個取捨為什麼可以接受**：真正會虧錢的三條路徑都不靠 L0 守。
下單只有 `engine/`（程式）能做、寫資料倉只有 `ingest_server.py`（token + hash chain）能做、
改風控規則要走 `RISK_RULES` H 節 → 你 `!approve` → WATCH 以 `apply_change.py` 寫入。
L0 守的是「Agent 亂改別人的檔案」，那是**可還原**的傷害，而 L3 就是為了還原而存在。

**這個取捨的真實成本**：
- FORGE 或 LAB 若真的繞道，**在被抓到之前那一瞬間它已經寫進去了**。L3 還原的是檔案，不是那次執行的副作用（例如它已經送出的 Discord 訊息）。
- `router/.env` 在 Windows 上沒有 OS 層的讀取保護。緩解：`.env` 只放 token，交易所 key 綁 IP，`watch-credential-check` 每日比對對外 IP。

**Router 會大聲告訴你現在是哪一種。** `preflight()` 在啟動時印出警告並說明目前的隔離層級，
不讓「以為有沙箱」這件事發生——那是比沒有沙箱更糟的狀態。

**想升級的時候**（不急，系統跑順了再說）：WSL2 是 Windows 內建功能，不是換作業系統。
`wsl --install -d Ubuntu-24.04` → 裝 `bubblewrap socat` → 專案搬到 WSL 的家目錄
（`\\wsl$\Ubuntu-24.04\...`，檔案總管照樣打得開）→ `router/.env` 的 `TD_REQUIRE_SANDBOX` 改成 `1`。
**不要**把專案放在 `/mnt/c/...`——跨檔案系統 I/O 會慢一個數量級，45 個排程任務每天都要讀寫。

### 2. 不採用「每個 Agent 一個 Windows 帳號 + ACL」

理由不是它不好，是投入產出：
- Router 要保管 15 組帳號憑證——這本身就是新的攻擊面，而且憑證要放哪？
- 檔案擁有權會變成維護惡夢（每次 `git checkout` 都可能改變 owner）
- Claude Code 的 session 資料、快取要 15 份
- 換來的額外保護，WSL2 的 L0 已經覆蓋了絕大部分，而且成本只有一次安裝

**這是判斷，不是事實。** 如果哪天實盤規模大到值得，這是下一步該做的事。

### 3. 還沒關上的洞：thread-history 旁路

Router 會把 thread 的近期訊息貼給任何被 @ 到的 Agent。
這繞過視圖授權——如果 CREATIVE 被拉進一個 TRADE_PLAN 的 thread，它會看到進場價。
L0 管不到這個（訊息是 Router 放進 prompt 的，不是檔案）。

- 現在的做法：**不要把 CREATIVE / GROWTH @ 進交易 thread**（人的紀律，不可靠）
- 計畫中的做法：`shared/view_grants.yaml` 加 `thread_visibility` 欄位，
  Router 依此過濾貼進 prompt 的歷史訊息

我把它留在這裡當作已知缺口，而不是假裝它不存在。

---

## 五、怎麼驗證邊界還在

```bash
python scripts/sync_sandbox.py --verify    # L0 與 OWNERSHIP.yaml 同步
python scripts/verify_isolation.py         # 四項保證 + 逃逸路徑報告 + L0 覆蓋率
python scripts/guard_paths.py status       # L3 基準涵蓋幾個檔
python scripts/lint_agents.py              # 21 項，含上面全部
```

`verify_isolation.py` 現在的輸出會明講逃逸路徑有沒有被 L0 封住：

```
⚠️ 工具層逃逸路徑（能寫檔 + 能執行任意程式 → 單靠 allow/deny 形同建議）：
  - forge：寫入 [...] 執行 [...] → 已由 L0 OS 沙箱封住
  - lab  ：寫入 [...] 執行 [...] → 已由 L0 OS 沙箱封住
  → L0 只在 macOS / Linux / WSL2 生效；原生 Windows 沒有沙箱
```

**這份報告永遠不會消失，也不該消失。** 它的存在是提醒：邊界是有條件的，條件寫在上面那行。

---

## 參考

- [Claude Code sandboxing — Anthropic Engineering](https://anthropic.com/engineering/claude-code-sandboxing)
- [Configure the sandboxed Bash tool — Claude Code Docs](https://code.claude.com/docs/en/sandboxing)
- [Securely deploying AI agents — Claude Code Docs](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- [Native sandbox support for Windows (non-WSL) — claude-code#46740](https://github.com/anthropics/claude-code/issues/46740)
- [Sandboxes and Worktrees: My secure Agentic AI Setup — Mike McQuaid](https://mikemcquaid.com/sandboxed-agent-worktrees-my-coding-and-ai-setup-in-2026/)
- [Git Worktrees Need Runtime Isolation for Parallel AI Agent Development](https://www.penligent.ai/hackinglabs/git-worktrees-need-runtime-isolation-for-parallel-ai-agent-development/)
- [bubblewrap](https://github.com/containers/bubblewrap) / [sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime)
