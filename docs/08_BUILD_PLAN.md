# 08 — 建置計畫：Blacksheep → CEO → FORGE

> 這份文件回答：**「我要透過 CEO 把整個系統建起來，實際上怎麼運作？我在 Discord 打什麼？」**
> 本檔同時是**建置待辦的唯一真相**——CEO 從這裡取任務，FORGE 完成後在這裡打勾。

## 一、無法委派的那一段（Bootstrap Floor）

先說清楚：**CEO 沒辦法建立 CEO 自己。** 在 Router 跑起來之前，沒有任何 Agent 收得到訊息。所以有一段約 **60–90 分鐘**的手動工作是不可省略的：

| # | 只能你做 | 為什麼 | 出處 |
|---|---|---|---|
| 1 | 安裝 Claude Code、`/login` | 是 Agent 的執行環境本身 | `02_SETUP_GUIDE.md` §2 |
| 2 | 解壓專案、建 venv、`pip install` | 沒有 Python 環境就沒有 Router | §3 |
| 3 | `build_context.py` → `init_db.py` → `lint_agents.py` | 產生 Agent 的規則切片與資料庫 | §3 |
| 4 | 在 Discord 建伺服器、18 個頻道 | 需要人類帳號操作 | `03_DISCORD_SETUP.md` |
| 5 | 建 16 隻 Bot、複製 token、開 Intent、邀請進伺服器 | Discord 開發者後台無 API 可自動化 | §5 |
| 6 | 填 `router/.env`、各 `USER.md` 的 Discord User ID | 金鑰只有你能持有 | §6 |
| 7 | 啟動 Router（`python router\discord_router.py`） | 這一刻起 CEO 才活著 | §8 |

**做完第 7 步，你就再也不用碰終端機了**（除了緊急狀況）。從第 8 步起全部透過 CEO。

> 走 `QUICKSTART.md` 可以先只建 2 隻 Bot（ROUTER + CEO），讓 CEO 先活起來，再請 CEO 指導你建其餘 14 隻——這是最快看到成果的路徑。

## 一之二、Day 0 逐步（照抄即可）

**回答「我是不是只要建 Discord + CEO，剩下交給 CEO？」——不完全是。** 分界線很清楚：

| CEO **能**自動做 | CEO **不能**做（只有你能） |
|---|---|
| 讀 `docs/08_BUILD_PLAN.md` 決定下一步 | 建 Discord Bot、複製 token、開 Intent（開發者後台無 API） |
| 派工給 FORGE 寫 `engine/`、`scripts/`、`backtest/`、`dashboard/` 的所有程式 | 填 `.env` 與各 `USER.md` 的 ID（金鑰只有你能持有） |
| 驗收（要求附 pytest / lint 實際輸出）、退件、追蹤 | 啟動 Router（在它跑起來之前沒有 Agent 存在） |
| 指導你建其餘 14 隻 Bot（一步一步問它） | Bitget API Key、Meta / Canva 授權、IG 轉商業帳號 |
| 依 `11_LEGACY_ASSETS.md` 安排舊專案程式的移植 | `!approve` 高風險交付（EXEC / RISK / LEDGER） |

專案的 `.md` 骨架、15 個 Agent 的人設與手冊、`shared/` 規格、Router、切片機制——**這些 zip 裡已經有了，CEO 不需要生成它們**。CEO 要建的是「還沒寫的程式」（Phase 2–7 的待辦），不是重新發明架構。

### 第 0 天：60–90 分鐘，照這個順序

```powershell
# ── 步驟 1：環境（各做一次）─────────────────────────────
PS> irm https://claude.ai/install.ps1 | iex
PS> claude                                    # /login 用 Claude Pro 帳號，然後 /exit
PS> claude -p "回覆 OK" --output-format json --model sonnet   # 確認非互動模式可用

# ── 步驟 2：部署專案 ────────────────────────────────────
PS> # 解壓 trade-desk.zip 到 C:\trade_desk
PS> cd C:\trade_desk
PS> python -m venv .venv; .\.venv\Scripts\Activate.ps1
PS> python -m pip install -r requirements.txt
PS> python scripts\build_context.py          # 生成 15 個 Agent 的規則切片
PS> python scripts\init_db.py                # 建資料庫
PS> python scripts\lint_agents.py            # 必須顯示「通過」才往下走
PS> mkdir $HOME\.claude\skills -Force; Copy-Item -Recurse -Force skills\* $HOME\.claude\skills\
PS> git init -b main; python scripts\install_git_hooks.py   # 先裝金鑰閘門再 commit
PS> python scripts\check_secrets.py --all; git add -A; git commit -m "bootstrap"

# ── 步驟 3：盤點舊專案（你已有的資產，越早做越省事）─────────
#    多個舊專案一律走登錄表，不要一個一個打路徑——同一種能力常有兩三個版本，
#    CEO 必須同時看到全部候選才選得對。
PS> Copy-Item legacy\projects.yaml.example legacy\projects.yaml
PS> notepad legacy\projects.yaml             # 每個專案一段：id / path / trust / proven / known_issues
PS> python scripts\scan_legacy.py --all      # 一次盤點全部，產生索引 + 能力對照表
PS> notepad docs\11_LEGACY_ASSETS.md         # 在「你的決定」欄填 PORT / REF / SKIP

# ── 步驟 4：Discord（先只建 2 隻 Bot：TD-ROUTER、TD-CEO）────
#    照 QUICKSTART.md 第 2 節；重點是 Message Content Intent 一定要開

# ── 步驟 5：填設定 ──────────────────────────────────────
PS> Copy-Item router\.env.example router\.env
PS> notepad router\.env                      # OWNER_USER_ID、GUILD_ID、兩個 TOKEN、CH_*
PS> notepad agents\ceo\USER.md               # 填你的 Discord User ID
PS> # 暫時把 agents.yaml 中 router / ceo 以外的 Agent 註解掉

# ── 步驟 6：啟動 ────────────────────────────────────────
PS> python router\discord_router.py
```

### 第 0 天結束時，在 `#human-inbox` 貼這三則

**① 確認 CEO 活著**
```
@TD-CEO !status
```

**② 交棒**
```
@TD-CEO 我是 Blacksheep。Router 已上線，目前只有 TD-ROUTER 與 TD-CEO 兩隻 Bot。
請讀 docs/08_BUILD_PLAN.md 與 docs/11_LEGACY_ASSETS.md，回報：
(1) 目前在哪個 Phase (2) 下一步 (3) 需要我先決定的事
(4) 我標記 PORT 的既有資產中，哪些可以直接抵掉 Phase 2–6 的待辦
```

**③ 讓 CEO 帶你建完其餘 14 隻 Bot**
```
@TD-CEO 我要建剩下 14 隻 Bot。請一次給我一隻的完整步驟
（Application 名稱、要開哪些 Intent、要勾哪些權限、token 填到 .env 的哪個變數），
我做完回報「done」你再給下一隻。
```

### 第 1 天起，你只需要三種指令

```
@TD-CEO 開始 Phase 2                          ← 推進階段
@TD-CEO !status                               ← 問進度
!approve FIX-2026-0912-003                    ← 核准高風險交付
```

## 二、CEO 主導的建置迴圈

```
Blacksheep 在 #human-inbox 說「開始 Phase 2」
   ↓
CEO 讀 docs/08_BUILD_PLAN.md，取出該階段未完成項目（同時 ≤ 2 項）
   ↓
CEO 在 #forge 發 TASK_ASSIGN @TD-FORGE
   （spec 指向 shared/ 的節次；acceptance 是可執行的指令）
   ↓
FORGE 實作 → 跑 pytest + lint → TASK_DONE（附實際輸出）
   ↓
CEO 驗收：測試過了嗎？符合規格嗎？
   ├─ 否 → REJECTED，說明原因，FORGE 重做
   └─ 是 → 高風險（EXEC/RISK/LEDGER）？
            ├─ 是 → @REDTEAM 審 → HUMAN_DECISION_REQUIRED → 你 !approve
            └─ 否 → REVIEW_RESULT，FORGE 在本檔打勾
   ↓
CEO 每日 08:35 在 #ceo-daily 發建置日報
```

## 三、你在 Discord 實際要打的字

### 開場（Router 起來後的第一則）
```
@TD-CEO 我是 Blacksheep。系統剛完成 bootstrap，Router 已上線。
請你讀 docs/08_BUILD_PLAN.md，確認目前處於哪個 Phase，並回報：
(1) 已完成什麼 (2) 下一步該做什麼 (3) 有沒有需要我先決定的事
```

### 推進一個階段
```
@TD-CEO 開始 Phase 2（資料基礎）。派工給 FORGE，一次最多兩項。
```

### 指定單一項目
```
@TD-CEO !task 請 FORGE 實作 engine/ingest_server.py，
驗收：tests/test_hashchain.py 通過、非法 token 被拒、lint 通過
```

### 問進度
```
@TD-CEO !status
```

### 核准高風險交付
```
!approve FIX-2026-0912-003
```

### 卡住時
```
@TD-CEO FORGE 那個任務卡兩天了，給我兩個解法選項和你的建議
```

### 你想自己動手時
```
@TD-CEO 我要自己在 dev/ 改 engine/executor.py，先幫我 !pause，
完成後我會告訴你，請你叫 FORGE 補測試
```

## 四、建置待辦（CEO 從這裡取任務；FORGE 完成後打勾）

> 規則：一次只推一個 P0；每個項目的 spec 都指向 `shared/` 的具體節次；驗收一律是可執行的指令。

### Phase 1 — 團隊上線（你手動，見第一節）
- [ ] Bootstrap Floor 第 1–7 步完成
- [ ] `@TD-CEO !status` 有回應（👀 → ⚙️ → ✅）
- [ ] CEO 能派工給 MACRO 並收回 `TASK_DONE`
- [ ] 16 隻 Bot 全數上線；工作排程器常駐並通過重開機測試

### Phase 0 — 資產複用盤點（在 Phase 2 之前做，可大幅縮短 2–6）
- [ ] `scripts/scan_legacy.py` 已對每個既有專案跑過，`docs/11_LEGACY_ASSETS.md` 已生成
- [ ] Blacksheep 已在「決定」欄標記 PORT / REF / SKIP
- [ ] 標記 PORT 的項目已由 CEO 轉成 `TASK_ASSIGN`（逐檔列出 `legacy_paths[]`，指定 `legacy-port` skill）
- [ ] 疑似含金鑰的檔案已清理，且舊 key 已在交易所端輪換
- [ ] CEO 在建置日報中標明：哪些 Phase 待辦因為移植而縮短或取消

### Phase 2 — 資料基礎（P0）
- [ ] `scripts/init_db.py` 已跑，`v_system_status` 可查　　spec: `db/001_schema.sql`、`db/002_views.sql`
- [ ] `engine/ingest_server.py`：唯一寫入口、token 驗證、hash chain　　spec: `shared/DATA_SCHEMA.md`　　驗收: `pytest tests/test_hashchain.py`；非法 token 回 401
- [ ] `scripts/collect_hourly.py`：T1 的 K 線／資金費率／OI／深度　　spec: `skills/market-data-collection`　　驗收: 跑一次後 `v_data_quality` 有 BTC/ETH 各時框且無缺口
- [ ] `scripts/compute_indicators.py`：EMA/ATR/RSI/VWAP/VolumeProfile/swing/structure/session_open　　驗收: `v_indicators` 每個 symbol×tf 都有最新值
- [ ] `scripts/refresh_universe.py`：依 `shared/universe.yaml` 的規則重算四層商品宇宙（T1/T2/T3/T4）　　驗收: 跑一次後 `v_universe` 的分層與 `universe.yaml` 的門檻一致，且 T1 仍含 BTC/ETH
- [ ] `engine/marketing_metrics.py`：把 IG / 內容數據寫進資料倉（走 ingest_server 的 token 驗證，不由 Agent 直寫）　　驗收: `v_marketing_metrics` 有當日資料且 hash chain 連續
- [ ] `scripts/merkle_anchor.py`、`crosscheck.py`、`backup.py`、`verify_chain.py`　　spec: `skills/data-integrity`　　驗收: `#audit-log` 出現 `AUDIT_ANCHOR`；還原測試成功
- [ ] `scripts/heartbeat_check.py`　　驗收: 故意停掉一個 job 會收到 `HEARTBEAT_ALERT`

### Phase 3 — 會分析（P1）
- [ ] `scripts/levels.py`：OB / FVG / 流動性 / 缺口 / POC / Fib 候選　　spec: `skills/smc-analysis`
- [ ] `scripts/patterns.py`：古典型態辨識（頭肩／雙頂底／三角／旗形／楔形／矩形）+ MSS 判定　　spec: `skills/pattern-analysis`、`strategy_params.analysis.patterns`　　驗收: 對已知型態的歷史區間能辨識出來；量價未確認的突破必須回報未通過
- [ ] `scripts/blind_pack.py` 必須早於 `redteam-htf-review` 上線（排程訊息已宣稱「Router 已附盲審包」）
- [ ] `scripts/prefilter_1h.py`：無候選輸出 `SKIP`　　驗收: 無匯合區時 CEO 的 `#analysis` 完全安靜（省額度的關鍵）
- [ ] `scripts/write_macro.py`、`calendar_update.py`　　spec: `skills/macro-briefing`、`skills/event-calendar`
- [ ] `scripts/write_plan.py`　　驗收: 寫入的 JSON 通過 `shared/schemas/trade_plan.schema.json`
- [ ] `scripts/blind_pack.py`：REDTEAM 盲審包　　驗收: 產出的包不含 `reasoning` 與 `confidence`
- [ ] MACRO 每日 brief、CHART 每日 HTF + 每小時掃描 連續運作 3 天

### Phase 4 — 會下單（P1，DEMO）
- [ ] `engine/bitget_client.py`：ccxt 封裝、速率限制、DEMO 切換、合約規格快取　　spec: `skills/bitget-execution`
- [ ] `engine/risk_gate.py`：G1–G15 + B 節倉位 + C 節帳戶檢查　　spec: `shared/RISK_RULES.md § A,G,B,C`　　驗收: `pytest tests/test_risk_gate.py`，每條規則各一個通過與一個拒絕案例　　**需 REDTEAM + Blacksheep 核准**
- [ ] `engine/ratchet.py`：R0–R4 / RH　　spec: `§ E`　　驗收: `pytest tests/test_ratchet.py`，SL 單調不回退
- [ ] `engine/executor.py`：下單、10 秒止損檢查、對帳、`!flatten`　　spec: `§ D`　　驗收: DEMO 完成一筆完整生命週期；連跑 24h 無對帳差異　　**需 REDTEAM + Blacksheep 核准**
- [ ] `engine/metrics.py` + `scripts/write_review.py`　　spec: `shared/METRICS_SPEC.md`　　驗收: 回測與實盤用同一函式

### Phase 5 — 會驗證（P2）
- [ ] `backtest/data_loader.py`：8 年資料、Binance 補齊、T3/T4 現貨拼接標基差
- [ ] `backtest/engine.py` + `walkforward.py` + `report.py`　　spec: `skills/backtest-walkforward`
- [ ] 第一份 `BACKTEST_REPORT` 通過 acceptance 且 REDTEAM 能 `--verify` 重跑出相同結果

### Phase 6 — 門面與治理（P2）
- [ ] `scripts/merge_fix.py`：唯一能合併到 `main` 的程式（verify → build_context → lint → pytest → merge → 建立 `router/RESTART_REQUESTED`）　　spec: `docs/10_CODE_GOVERNANCE.md` §1.1　　驗收: FORGE 無法自行合併；任一步失敗即不合併
- [ ] `scripts/apply_change.py`：接 `!approve`，寫 `config_versions`、遞增 `strategy_params.version`、打 `params-v<n>` tag　　驗收: `!approve CHG-x` 後 `config_versions` 多一列且版本號遞增
- [ ] `scripts/rollback.py`：revert → build_context → lint → 重啟 → `#forge` 發 FIX_ROLLBACK　　spec: §1.4
- [ ] `scripts/install_skills.py` + lint 比對：`~/.claude/skills/` 與 repo 的 SKILL.md 雜湊必須一致　　spec: §3.4　　驗收: 改了 repo 的 skill 但沒重裝 → Router preflight 失敗
- [ ] `scripts/scan_secrets.py` + `.git/hooks/pre-commit`：擋住含金鑰的 commit　　驗收: 故意寫入假 key 後 commit 被拒
- [ ] `engine/executor.py recover` 子命令：開機對帳補止損　　spec: `docs/05_OPERATIONS.md` 災難情境　　驗收: 手動 kill Router 後重啟，缺失的 SL 在 30 秒內補上

- [ ] `dashboard/app.py` + `static/index.html`　　驗收: 顯示資產、持倉、15 張 Agent 卡片、額度條
- [ ] `scripts/usage.py`　　驗收: 額度剩 20% 時發預警
- [ ] `scripts/task_db.py`（含 `--precheck`）、`feed_status.py`、`creative_gate.py`
- [ ] DEMO 模式連跑 7 天無人工介入

### Phase 7 — 行銷（P3）
- [ ] IG 轉專業帳號 + 綁粉專 + Meta App（**你手動**，見 `02_SETUP_GUIDE.md` §13）
- [ ] `scripts/render_chart.py`、`publisher.py`、`ig_insights.py`、`trends.py`
- [ ] CREATIVE 產出草稿 → `!publish` 成功發佈一篇 → GROWTH 抓回 Insights

### Phase 8 — 決策點
- [ ] 累積 4 週 DEMO、交易數 ≥ 30 筆
- [ ] DEMO 期望值 ≥ 回測樣本外 × 60%
- [ ] `!flatten` 與 C1–C4 熔斷各測試過一次
- [ ] 對帳連續 7 天無差異
- [ ] **Blacksheep 決定是否進入真錢 20% 資金階段**

## 五、什麼時候該跳回 `dev/` 自己動手

CEO 主導是預設路徑，但以下情況直接自己來比較快：

| 情況 | 為什麼 |
|---|---|
| **Router 或 FORGE 本身壞了** | 修理工壞了不能叫修理工修；這是 `dev/` 存在的首要理由 |
| 同一個 bug FORGE 試了兩次還沒解 | 透過 Discord 除錯的來回成本太高 |
| Claude Pro 額度用完 | FORGE 動不了，但你可以 |
| 你只是想快速試個想法 | 不值得走完整的任務流程 |
| 需要看終端機即時輸出除錯 | Discord 收不到 stdout 串流 |

自己動手前先跟 CEO 說一聲（範本見第三節最後一則），完成後請它叫 FORGE 補測試與文件，指揮鏈才不會斷。

## 六、Token 現實（Claude Pro）

建置任務比營運任務貴得多——實作 `engine/executor.py` 可能要 30–40 分鐘的 `claude -p`。實務估計 **[估計]**：

- FORGE 每天大約能完成 **1–2 個中等項目**，前提是不與交易時段的 Agent 搶額度。
- 建議把建置任務排在**盤面較安靜的時段**，或在建置期先把 `scheduler.yaml` 的 `chart-1h` 停用。
- Phase 2–6 在 Pro 額度下**估計 6–10 週**；升級 Max 5x 大約可壓到 3–4 週。
- WATCH 的 `!budget` 隨時可查用量；額度剩 20% 時 WATCH 預警、Router 依 llm_budget.priority 延後非關鍵 Agent。

若你希望更快，最務實的組合是：**Phase 2–4 你在 `dev/` 自己寫（快），Phase 5 起交給 CEO/FORGE（省你的時間）**。這不違反任何設計——`dev/` 與 CEO 路徑本來就是互補的。
