# 05 — 日常維運

> 這份文件回答：**「系統跑起來之後，我每天／每週要做什麼？出事怎麼辦？」**

## 交易日邊界：台北 08:00

**台北 08:00＝00:00 UTC＝日 K 收線。** 這一刻同時發生四件事：

- 日 K 收線（週一同時收週 K，1 號同時收月 K）
- `RISK_RULES` C1 的「單日已實現＋未實現虧損 ≥ 3% 停開新單」計數歸零
- 所有報表裡「昨日／本月」的定義換日
- 高時框分析（HTF）第一次有完整的新日線可用

因此早晨這一段是**順序敏感**的，不能為了平衡額度亂搬：

| 時間 | 任務 | 為什麼是這個順序 |
|---|---|---|
| 08:01 | `feed-collect` | 收線後第一根完整日 K 落庫 |
| 08:03 | `feed-indicators` | 指標要用剛落庫的日 K |
| 08:08 | `chart-htf`（opus） | 有 `daily_close_check.py` precheck：日／週／月 K 與指標都到位才觸發 |
| 08:20 | `audit-daily` | 交易日已結算，才算得出「昨日」績效 |
| 08:35 | `ceo-daily-report` | 匯總前面三份產物 |
| 08:40 | `chart-htf-retry` | 08:08 因資料未到位 SKIP 時的補跑（與 `chart-htf` 互斥，額度只計一次） |

月報同理：**月 K 也是在 1 號台北 08:00 才收線**，所以 `audit-monthly` 排在 1 號 23:50，不會排在月初凌晨。

## 每日（3 分鐘）
1. 看 `#ceo-daily` 的每日總匯報（08:35 發出）。
2. 處理 `HUMAN_DECISION_REQUIRED`——CEO 只能提案，等你回覆。
3. 看 `#marketing-review` 的內容草稿（15:00 起），`!publish <id>` 或 `!reject <id> <原因>`。
4. 掃一眼 `#alerts`。沒有紅字就結束。

## 每週（20 分鐘）
1. 週日 21:00 的週會 thread（`#meeting-room`），你可以旁觀或插話。
2. 看四份週報：AUDIT 止損解剖、RISK 風控、GROWTH 成長、WATCH 系統健康。
3. 決定 LAB 的研究提案要不要立項。
4. 確認備份的 `restore_test_ok = 1`。

## 每月
- FEED 重算 T2 名單 → 你確認 `UNIVERSE_UPDATE`。
- AUDIT 簽發月度績效報表（CREATIVE 才能引用它做績效透明貼文）。
- REDTEAM 壓力情境檢討。
- FORGE 的 `lint_agents.py` 月報。
- 更新 Meta 長期 token（60 天到期，GROWTH 會提前 7 天提醒）。

## 常用指令

### Owner 在 Discord `#human-inbox`
| 指令 | 效果 |
|---|---|
| `!status` | CEO 立即回報摘要 |
| `!task <描述>` | 請 CEO 立項 |
| `!approve <change_id>` | 核准變更／策略上線 |
| `!pause` / `!resume` | 停止／恢復開新單 |
| `!flatten` | 撤所有單、市價平所有倉 |
| `!unlock` | 解除 12% 回撤停機 |
| `!publish <content_id>` / `!reject <id> <原因>` | 內容發佈／退回 |
| `!budget` | WATCH 回報 Claude 用量 |
| `!agents` | WATCH 回報 15 個 Agent 狀態 |

### 在 PowerShell
```powershell
cd C:\trade-desk; .\.venv\Scripts\Activate.ps1

python scripts\build_context.py            # 改完 shared/ 必跑
python scripts\build_context.py --verify   # 驗證一致性
python scripts\lint_agents.py              # Agent 定義自洽檢查（含排程負載與手冊排程一致性）
python scripts\sync_manual_cron.py         # 改完 scheduler.yaml 必跑：重生 15 份手冊的排程行
python scripts\init_db.py                  # 建庫／套用 migration
python router\discord_router.py            # 前景啟動（除錯用）
Get-Content logs\router.log -Tail 50 -Wait # 看即時日誌
```

## 啟動與停止
- **啟動**：Windows 工作排程器「登入時執行」自動啟動；或 `router\start.ps1`。
- **停止**：關掉 Router 的 process（`Stop-Process -Name python`）。**注意**：Router 停了不代表倉位平掉——交易所的止損單仍在。要平倉請下 `!flatten`（Router 還活著時）或到 Bitget 網頁手動處理。
- **重啟後**：Router 會跑 preflight（上下文完整性 + lint），不通過就不啟動並在日誌說明原因。

## 改排程的規則

`router/scheduler.yaml` 的檔頭有七條規則（R1–R7）。改完**一定要跑 `python scripts/lint_agents.py`**——第 12 項會檢查 5 小時窗的負載，違反就是 ERROR。

第 12 項算的是**最壞情況**：每個「幾號」的月報都可能落在任何星期幾，所以它會把「每日 × 該星期的週報 × 該號的月報」三者疊起來檢查（1 號可能是週日）。只看單日排程表會漏掉這種疊加。

快速看目前分佈：
```powershell
python -c "import yaml;s=yaml.safe_load(open('router/scheduler.yaml',encoding='utf-8'));[print(f\"{j['cron']:16} {j['name']}\") for j in sorted(s['jobs'],key=lambda x:x['cron'])]"
```

| 想加新的排程任務 | 怎麼選時段 |
|---|---|
| opus 任務 | 幾乎沒有空檔：目前 opus 任務：每日 08:08（chart-htf）、每日 13:30（redteam-htf）、週日 21:00（週會）、5 號 02:10（壓力測試）、季審 8 號 02:10（redteam-quarterly）；另有 08:40 的 chart-htf-retry（互斥，權重 0）。新的要離所有既有 opus ≥ 5 小時 |
| sonnet 任務 | **07:30–12:30 完全不能加**（早晨窗已滿 6.0，那是交易日邊界，不可讓路）；13:30–18:30 只剩 2.0（redteam opus 3 + creative 1 已佔 4.0）；18:40 之後最寬 |
| 週報類 | 週六（18:40 起四件：lab / audit / risk / macro）比週日（18:40 起四件＋21:00 opus 週會）空 |
| 月報類 | 1–4 號固定 23:50（月 K 台北 08:00 才收線，不能排凌晨），5 號 02:10 給 opus 壓力測試 |
| 程式型任務 | 不計入權重，隨時可加 |

## 升級
| 升級什麼 | 步驟 |
|---|---|
| Claude Code | `claude update`，然後 `claude -p "ok"` 測試，再重啟 Router |
| Python 套件 | 在 `dev/` 更新 `requirements.txt` → `pip install -r` → 跑 `pytest` → 重啟 Router |
| 策略參數 | 走變更流程：LAB 回測 → REDTEAM 審 → RISK 簽核 → 你 `!approve` → WATCH 寫入 |
| Agent 手冊／人設 | 在 `dev/` 改 → `lint_agents.py` → Router 下次呼叫自動生效（不用重啟） |
| `shared/` 規格 | 改 → `build_context.py` → `lint_agents.py` → 重啟 Router |
| `agents.yaml` / `scheduler.yaml` | 改 → 重啟 Router |

## 故障排除

| 症狀 | 先看 | 處理 |
|---|---|---|
| Bot 上線但不回應 @ | Message Content Intent 是否開啟；`.env` 的 `GUILD_ID` | 補開 intent，重啟 Router |
| 👀 出現但一直 ⚙️ | `logs\router.log` | LAB/FORGE 可跑 40 分鐘屬正常；否則多半是 Claude 登入過期 → `claude` → `/login` |
| ❌ 且 `#forge` 出現 BUG_REPORT | FORGE 的分析 | 這是正常路徑，等 FORGE 提 FIX_PROPOSAL |
| Router 啟動失敗，說 preflight 失敗 | 錯誤訊息 | 多半是改了 `shared/` 沒重建切片 → `build_context.py` |
| Agent 回「上下文完整性驗證失敗」 | 同上 | 同上 |
| 查詢被拒「未被授權存取」 | `shared/view_grants.yaml` | 這是設計。真的需要就發 SKILL_REQUEST 給 FORGE 新增視圖 |
| 排程沒觸發 | Router 是否在跑、cron 語法、時區 | `openclaw` 無關；看 `logs\router.log` 的 scheduler 行 |
| 額度用完（⏳） | `#agent-health` | 等窗口重置；或考慮 Max 5x |
| IG 發佈 400 | 圖片是否公開可讀的 JPEG、比例 4:5–1.91:1、token 是否過期 | 更新 token 或修圖 |
| 對帳不一致 | `#execution` 的 RECONCILE_ALERT | 系統會自動停開新單；到 Bitget 核對後手動處理 |

## 災難情境

| 情境 | 立即動作 |
|---|---|
| 帳戶大幅虧損 | `!flatten` → `!pause` → 看 AUDIT 的解剖 |
| 懷疑資料被竄改 | `python scripts\verify_chain.py`；對照 `#audit-log` 的每日 Merkle root |
| Router 反覆崩潰 | 停掉工作排程器的 watchdog，前景跑 `python router\discord_router.py` 看完整錯誤 |
| 電腦重灌 | 走 `docs/10_CODE_GOVERNANCE.md` §2.3 的裸機還原七步（重點：**先 `executor.py recover` 對帳補止損，再啟動 Router**） |
| API key 外洩 | 走 `docs/10_CODE_GOVERNANCE.md` §4 的止血四步：先斷 → 查版控 → 補新 key → 記錄 |
| **斷電／重開機** | Router 不會自己回來（需使用者工作階段）。開機後：登入 → Router 自動啟動 → **preflight 通過後強制跑 `python engine\executor.py recover`**：從交易所拉倉位與掛單對帳，任何無止損的倉位 30 秒內補掛，對不上就 `system_state.trading = HALT` 並 @Blacksheep。建議加 UPS，至少撐到優雅關機（讓 WAL checkpoint 完成） |
| **Discord 連不上** | 這是唯一的通道，但**交易不受影響**（EXEC 與 Risk Gate 是純程式）。系統行為：連續 15 分鐘送不出訊息 → 自動 `system_state.trading = NO_NEW_ENTRY`（不平倉、只停開新單），未送出的訊息寫 `logs\undelivered.jsonl`，恢復後補送。**你的離線出口**：`python engine\executor.py flatten --local`（不經 Discord 的緊急平倉），或直接到 Bitget 網頁平倉 |
| **資料庫損壞**（`database disk image is malformed`） | 五步：① 停掉所有寫入行程（Router、ingest、executor、dashboard）② `sqlite3 data\tradedesk.db ".recover" > recover.sql` ③ 還原最近一次 `restore_test_ok = 1` 的備份 ④ 用 `#audit-log` 的每日 Merkle root 判定遺失區間 ⑤ FEED 重抓該區間，差異寫 `corrections` 表（**不覆蓋原列**） |
| **Router 崩潰迴圈** | watchdog 同一小時重啟 ≥ 3 次會停止重啟並直接 @Blacksheep（不再靜默）。前景跑 `python router\discord_router.py` 看完整錯誤 |

## `system_state.trading` 狀態機

| 狀態 | 意思 | 誰設 | 怎麼解除 |
|---|---|---|---|
| `RUNNING` | 正常 | 初始值 | — |
| `NO_NEW_ENTRY` | 不開新單，既有倉位照常管理（棘輪、止損都還在跑） | C1 日虧 3%／C2 週虧 6%／C3 連 4 敗（程式）、Discord 中斷 15 分鐘（heartbeat） | C1–C3 到期自動解除（下一個交易日邊界）；Discord 恢復自動解除 |
| `HALT` | 完全停止，含平倉授權 | C4 回撤 12%／C7 對帳不一致或 API 連 3 次失敗（程式）、資料庫完整性失敗（LEDGER） | **只能由 Blacksheep `!unlock`**（EXEC 執行，寫入稽核紀錄） |

**收到 `RECONCILE_ALERT` 或 P0 `DATA_ALERT` 時**：WATCH 必須在 60 秒內於 `#alerts` @Blacksheep，並確認 `system_state.trading` 已被設為 HALT；未設就自己設並記錄原因。

## 繞過 CEO 的直達清單

CEO 是唯一窗口，但**這些事必須由程式直接 @Blacksheep，不經 CEO 彙整**（CEO 漏報時訊號要有第二條路）：

C4／C7 熔斷 · 對帳不一致 · 資料庫損壞或 hash chain 驗證失敗 · Router 崩潰迴圈 · `.context` 驗證失敗 · 主任務與其互斥備援雙雙 SKIP（R7）· 金鑰即將到期或對外 IP 變動。
