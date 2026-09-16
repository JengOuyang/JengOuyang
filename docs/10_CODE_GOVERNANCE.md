# 10 — 版控、備份與汙染防治

> 這份文件回答：**「AI 每天在改我的程式，我怎麼確保改壞了能救回來、金鑰不會外洩、而且它們不會互相污染？」**
> 這是整個系統唯一沒有 Agent 負責的層級——**它保護的是系統本身**。

---

## 一、版本控制

### 1.1 分支模型（刻意極簡）

| 分支 | 誰能寫 | 意義 |
|---|---|---|
| `main` | **只有 `scripts/merge_fix.py`** | Router 正在執行的程式碼。任何時刻 `main` 都必須是可運行的 |
| `fix/<bug_id>` | FORGE | 一個 bug 一條分支 |
| `feat/<skill_or_module>` | FORGE / LAB | 一個功能一條分支 |
| `exp/<hypothesis>` | LAB | 回測實驗，通常不合併，只保留報告 |

**FORGE 與 LAB 不能合併自己的分支**——它們的 `settings.json` deny 了 `Bash(git push *)`、`Bash(git reset *)`、`Bash(git checkout main*)`。合併只能由 CEO 觸發 `scripts/merge_fix.py`，該程式依序執行：
`verify_delivery.py --worktree` → `build_context.py` → `lint_agents.py` → `pytest` → merge → 建立 `router/RESTART_REQUESTED` 旗標（watchdog 偵測後優雅重啟）。任一步失敗就不合併。

> **為什麼不用 PR 流程**：只有一個人類審核者，PR 只是多一層 UI。真正有效的是「合併前必須通過的那串指令」，而那串指令由程式執行、不由交付者自己宣稱。

### 1.2 一定要有 remote

`git init` 之後**當天**就設定私有 remote（GitHub private repo 或自架 Gitea）：

```powershell
git remote add origin https://github.com/<你的帳號>/trade-desk-private.git
git push -u origin main
```

`router/watchdog.ps1` 每日 `git push --all --tags`。**沒有 remote 的 git 只是本機資料夾的另一個副本**——SSD 掛了就一起沒了。

### 1.3 Tag：讓事故可以回溯到座標

| Tag | 什麼時候打 | 誰打 |
|---|---|---|
| `params-v<n>` | 每次 Blacksheep `!approve` 參數變更 | `scripts/apply_change.py`（與 `config_versions.version` 一一對應） |
| `live-<tier>` | 每次啟用新商品層（T2 / T3 / T4） | 人工 |
| `live-start` | 第一次進真錢 | 人工 |
| `incident-<date>` | 每次事故當下 | 人工，事後回溯用 |

事故回溯的第一個問題永遠是「那天跑的是哪一版參數」。有 tag 就是一條指令：`git show params-v7:shared/strategy_params.yaml`。

### 1.4 回滾

`scripts/rollback.py <commit|tag>` 四步：`git revert` → `build_context.py` → `lint_agents.py` → 觸發重啟 → 在 `#forge` 發 `FIX_ROLLBACK`。

**觸發回滾的條件（不需要討論，符合就回滾）**：

- 合併後 24 小時內出現同類 ❌
- 對帳出現差異
- 未完成 24 小時 DEMO soak 就進了 LIVE

**資料庫不回滾。** 資料倉是 append-only + hash chain，回滾會破壞鏈。錯誤的資料列用 `corrections` 表更正（原列保留，新增一列指向它並說明原因）——這是唯一合法的「改資料」方式。

---

## 二、備份三層

單顆 SSD 故障 = 程式、8 年資料、hash chain、`router/.env` 一起消失。所以三層：

| 層 | 內容 | 頻率 | 位置 |
|---|---|---|---|
| **L1 程式碼** | git（含 tag） | 每次合併 + 每日 push | 私有 remote |
| **L2 資料倉** | `.backup` API 產生的 `tradedesk_YYYYMMDD.db` + Parquet 匯出 | 每日 00:20（`ledger-backup`） | 第二顆實體磁碟 + rclone 雲端，保留 90 天 |
| **L3 金鑰** | `router/.env` 加密後（`age` 或 7z AES） | 每次變更 | 離線隨身碟 + 密碼管理器 |

### 2.1 備份前必做的兩件事

`scripts/backup.py` 在複製之前必須：

```sql
PRAGMA integrity_check;              -- 失敗 = 資料庫已損壞，立刻 P0 DATA_ALERT 並停開新單
PRAGMA wal_checkpoint(TRUNCATE);     -- 不做這步，備份會缺最近的寫入
```

**絕對不要用檔案複製備份 SQLite**（WAL 還在外面）。用 `.backup` API。

### 2.2 還原測試不是打勾，是真的還原

每週日：還原最新備份到 `data/restore_test/` → 跑 `verify_chain.py` → 跑三個 `v_*` 查詢 → 寫 `backups.restore_test_ok`。
**連兩週 `restore_test_ok != 1` → WATCH 發 P1。**

**進真錢的前置條件之一是「你親手演練過一次完整還原」**（見 `06_ROADMAP.md`）。沒演練過的備份，等於沒有備份。

### 2.3 裸機還原清單（電腦重灌／換機）

1. 裝 Python 3.12、Node LTS、Git、Claude Code；`claude` → `/login`
2. `git clone <私有 remote>` → `cd trade-desk` → 建 venv → `pip install -r router\requirements.txt`
3. 從離線隨身碟解密還原 `router/.env`（**Discord token 若曾外洩則全部重新產生**）
4. 從 L2 還原最新 `tradedesk_YYYYMMDD.db` 到 `data/`
5. `python scripts\build_context.py` → `python scripts\lint_agents.py` → 兩者都要通過
6. `python engine\executor.py recover` —— **先對帳再啟動**：從交易所拉現有倉位與掛單，補上缺失的止損
7. 啟動 Router，確認 `@TD-CEO !status` 有回應

---

## 三、汙染防治

系統裡有四種「會互相污染」的東西，各有各的隔離手段：

### 3.1 開發 session vs Agent session

`dev/` 與 `agents/` 是**兄弟目錄**，根目錄**不得有 `CLAUDE.md`**（lint 第 11 項會擋）。你在 `dev/` 開的 Claude Code session 讀 `dev/CLAUDE.md`（開發流程），Agent 讀 `agents/CLAUDE.md`（角色共同層）。兩條繼承鏈沒有交集——這是 ADR-004 的決定。

### 3.2 Agent 之間

- **規則**：`shared/` 是單一真相，`build_context.py` 為每個角色生成切片。**切片自身也有 SHA-256**（`MANIFEST.json` 的 `outputs`），直接改切片檔會被 `--verify` 抓到。所有 Agent 的 `settings.json` deny 了 `Write(.context/**)`。
- **資料**：`view_grants.yaml` + `query_readonly.py`，權限在 SQL 視圖層完成。
- **檔案**：deny `Read(../../agents/*/PERSONA.md|MANUAL.md|.context/**)`。
- **thread 歷史**：這是**唯一還沒補上的旁路**——Router 會把 thread 最近的訊息貼給被 @ 的 Agent，繞過視圖權限。已列入待辦（`view_grants.yaml` 的 `thread_visibility`），在那之前：**不要把 CREATIVE/GROWTH @ 進有 TRADE_PLAN 的 thread**。

### 3.3 生成物 vs 手寫檔

| 生成物 | 生成者 | 絕對不要手改 |
|---|---|---|
| `agents/*/.context/*` | `build_context.py` | 改了會被雜湊驗證抓到，Router 拒絕啟動 |
| 各 MANUAL 的 `[CRON:]` 行 | `sync_manual_cron.py` | 改了 lint 第 13 項會擋 |
| `docs/11_LEGACY_ASSETS.md` 的表格 | `scan_legacy.py` | 只有「決定」欄是給你填的 |
| 文件裡的數字 | `verify_docs_claims.py --fix` | 改了 lint 第 15 項會擋 |

### 3.4 共享狀態（一台機器上最容易被忽略的汙染源）

| 共享的東西 | 風險 | 處置 |
|---|---|---|
| `~/.claude/skills/` | 開機那天複製過去就不再同步——FORGE 改了 repo 的 skill，Agent 還在跑舊版 | 用 `scripts/install_skills.py` 安裝並寫 manifest；lint 比對雜湊，不同步就不讓 Router 啟動 |
| `.venv/` | 在 `dev/` 升級 `ccxt` 會立刻改變運行中 Router 的行為 | 升級套件前先 `!pause`，升完跑 `pytest` 再 `!resume` |
| user-scope 的 MCP（Canva） | `claude mcp add --scope user` 等於 15 個 Agent 都拿得到 | 只有 CREATIVE 需要；改用 `--scope project` 或在 `agents.yaml` 以 `mcp_config` 指定 |
| SQLite 單一檔案 | Router、ingest、executor、dashboard、15 個 Agent 同時開 | WAL 模式 + 只有 ingest 能寫；查詢一律 `mode=ro` + `PRAGMA query_only=1` |

### 3.5 權限隔離的四層與它的極限（誠實說）

你要的是「每個 Agent 絕對無法更動不屬於它的東西」。**用 Claude Code 的 allow/deny 做不到絕對**，
原因很單純：那是**工具層**授權，不是作業系統沙箱。任何同時擁有「寫檔」與「執行任意程式」的 Agent，
理論上都能寫一支腳本再執行它。`scripts/verify_isolation.py --escapes` 會把這種組合直接列出來：

```
⚠️ 工具層逃逸路徑
  - forge：寫入 Write(worktree/**)      執行 Bash(python worktree/*)
  - lab  ：寫入 Write(../../backtest/**) 執行 Bash(python ../../backtest/*)
```

這兩個是**設計上必要**的（FORGE 要寫程式、LAB 要寫回測），不能拿掉。所以隔離是四層：

| 層 | 機制 | 擋得住什麼 | 擋不住什麼 |
|---|---|---|---|
| **L0 作業系統層** | Claude Code 內建 sandbox（Linux/WSL2 用 bubblewrap、macOS 用 Seatbelt）。規則由 `scripts/sync_sandbox.py` 從 `OWNERSHIP.yaml` 生成，lint 第 21 項驗證；Router 另以 `--settings` 帶上 `strictAllowlist` / `allowUnsandboxedCommands:false` / `failIfUnavailable:true` | **Bash 指令與其所有子程序**——上面那兩條逃逸路徑真正被封住的地方；同時擋掉 `~/.ssh`、`router/.env` 的讀取與外網連線 | Read/Write/Edit 這些內建工具（走 L1 權限系統，不經過沙箱）；**原生 Windows 完全不存在這一層** |
| **L1 工具層** | 15 份 `settings.json` 的 allow/deny，由 lint 第 14 項強制基線 | 13 個 Agent 的全部寫入；所有人對 `shared/`、`.context/`、`.env`、`data/` 的直接寫入 | 有執行權的 Agent 繞道 |
| **L2 執行層** | FORGE 只能寫 `agents/forge/worktree/`（git worktree），LAB 只能寫 `backtest/`；**合併只能由 `merge_fix.py`**，兩者都 deny `git push` / `reset` / `merge` | 沙箱內的錯誤流進活動樹 | 沙箱內自殘（可接受，丟掉重來即可） |
| **L3 偵測層** | `scripts/guard_paths.py`：Router 每次呼叫 Agent **前後**比對 201 個受保護檔案的 SHA-256；未授權變更**自動 `git checkout` 還原**並回報 | 前兩層漏掉的一切，包含繞道 | 無法阻止「發生」，只能阻止「留下」 |

**L3 是偵測 + 自動回滾，不是預防；L0 才是預防。** 兩者都要，因為它們涵蓋的範圍不重疊：
L0 管 Bash 子程序，L1/L3 管內建工具。

#### 執行環境的前提：必須跑在 WSL2

L0 只在 macOS / Linux / **WSL2** 生效，**原生 Windows 不支援**。
更糟的是沒有沙箱時 `deny Read(router/.env)` 擋得住 Read 工具卻擋不住 `Bash(cat router/.env)`。
因此 `DAY0_RUNBOOK.md` 步驟 0 把「裝 WSL2」放在所有事情之前，
Router 也以 `failIfUnavailable: true` 讓沙箱起不來時**啟動即失敗**，而不是靜默降級成沒有保護。
選擇原生 Windows 是可以的，但那等於明知地放棄 L0——完整對照見 `docs/12_DIGITAL_BOUNDARY.md`。

#### 為什麼仍然不做「每個 Agent 一個 Windows 帳號 + ACL」

| | 效果 | 代價 |
|---|---|---|
| 每 Agent 一個 OS 帳號 + ACL | 連內建工具也擋得住 | 15 個本機帳號、每個帳號各自的 Claude Code 登入與 `~/.claude/`（額度與 session 都會分裂）、Router 需要提權、排錯難度大幅上升 |
| 現行四層 | L0 預防 Bash 子程序 + L1 擋工具呼叫 + L2 隔離沙箱 + L3 偵測全部並自動還原 | 一次 WSL2 安裝 |

**判定：L0 補上之後更不值得了**——它覆蓋了 OS 帳號方案絕大部分的價值。
但這仍是判斷不是事實：若哪天你讓這套系統管理他人資金，這個判斷就該重新做一次。

---

## 四、金鑰治理

`router/.env.example` 是唯一的變數清單（不含值）。實際持有的憑證與其效期：

| 憑證 | 效期 | 到期／異常的徵兆 | 誰提醒 |
|---|---|---|---|
| 16 個 Discord token | 永久（除非 reset） | Bot 離線 | WATCH 心跳 |
| Bitget API key | 永久，但**綁 IP** | 家用浮動 IP 變動 → 靜默 401 | `watch-credential-check` 每日比對對外 IP |
| Meta 長期 token | 60 天 | IG 發佈 400 | GROWTH 提前 7 天 |
| Canva OAuth | 會過期 | CREATIVE 產圖失敗 | 目前無人負責——由 FORGE 的 BUG_REPORT 發現 |
| Claude Code OAuth | 會過期 | 所有 LLM Agent 一起 ❌ | WATCH；處置是 `claude` → `/login` |
| `INGEST_TOKEN_*` | 永久 | ingest 回 401 | LEDGER |

**每 90 天輪換 Bitget key 與 Discord token**（寫進每月清單）。輪換順序：先產新 key → 更新 `.env` → 重啟 Router → 確認一筆 DEMO 下單成功 → 才刪舊 key。

### 金鑰外洩的止血順序

1. **先斷**：Bitget 後台刪除該 key（本專案的 key 無提幣權限，損失有限但仍要斷）
2. **再查**：`git log -S "<key 片段>"` 確認有沒有進過版控；有的話 remote 也要處理
3. **後補**：產新 key → 更新 `.env` → 重啟 → 驗證
4. **記錄**：在 `#alerts` 留下時間線，季審時檢討為什麼會外洩

---

## 五、這一層的自我檢查

```powershell
python scripts\lint_agents.py            # 14 項：settings.json 的 deny 基線與 model 別名
python scripts\verify_docs_claims.py     # 15 項：文件宣稱 vs 實際
git status --porcelain                   # 應該是空的；不是就代表有人手改了生成物
git log --oneline -5                     # 最近五次合併是誰、為什麼
```

**每月至少做一次**：`git log --all --oneline --since="1 month ago" | wc -l` 與 `#forge` 的 FIX_PROPOSAL 數量對得上嗎？對不上代表有人繞過了合併流程。
