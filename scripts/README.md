# scripts/ — 排程任務與工具程式

| 檔案 | 誰用 | 狀態 |
|---|---|---|
| `build_context.py` | FORGE / 你 | ✅ 已實作：從 shared/ 生成角色切片，`--verify` 檢查一致性 |
| `lint_agents.py` | FORGE / Router preflight | ✅ 已實作：33 項自洽檢查 |
| `query_readonly.py` | 所有 LLM Agent | ✅ 已實作：唯讀查詢 + 視圖權限強制 |
| `init_db.py` | 你（第一次） | ✅ 已實作 |
| `collect_hourly.py` | FEED | ⬜ 待實作 |
| `compute_indicators.py` | FEED | ⬜ |
| `refresh_universe.py` | FEED（每月 T2 名單） | ⬜ |
| `levels.py` | CHART（OB/FVG/Fib/POC 候選） | ⬜ |
| `prefilter_1h.py` | Router（無候選輸出 SKIP，省額度） | ⬜ |
| `merkle_anchor.py` / `crosscheck.py` / `backup.py` / `verify_chain.py` | LEDGER | ⬜ |
| `write_macro.py` / `write_plan.py` / `write_review.py` / `write_marketing.py` | 各 Agent 寫入資料倉 | ⬜ |
| `calendar_update.py` | MACRO（事件日曆，含 `--precheck-4h`） | ⬜ |
| `heartbeat_check.py` / `usage.py` | WATCH | ⬜ |
| `task_db.py` | CEO（任務板，含 `--precheck`） | ⬜ |
| `render_chart.py` / `publisher.py` / `ig_insights.py` / `trends.py` / `gsc.py` | 行銷 | ⬜ |
| `blind_pack.py` | Router（產生 REDTEAM 的盲審包） | ⬜ |
| `render_report.py` | LAB/AUDIT/FORGE/CEO/GROWTH/CMO（長輸出轉互動 HTML，見 `skills/report-preview`） | ⬜ |
| `verify_delivery.py` | CEO/REDTEAM 獨立驗收交付（不相信交付者自報的測試結果） | ✅ 已實作 |
| `feed_status.py` / `creative_gate.py` | 程式型 Agent 的 on_mention | ⬜ |
| `sync_sandbox.py` | FORGE / lint 21 | ✅ 已實作：由 OWNERSHIP.yaml 生成 15 份 OS 層沙箱設定（L0） |
| `check_secrets.py` | git pre-commit / CI | ✅ 已實作：金鑰閘門（私有庫在 GitHub Free 沒有 push protection） |
| `install_git_hooks.py` | Owner（Day 0 一次） | ✅ 已實作：裝 pre-commit / pre-push / post-commit |
| `backup_mirror.py` | Owner（每週） | ✅ 已實作：git bundle + 鏡像 clone + .env 鍵名清單（3-2-1 的第 2、3 份） |
| `build_docs_html.py` | Owner / FORGE | ✅ 已實作：深色 + 側邊導覽的白皮書 HTML；`--check` 驗 Markdown 表格結構（lint 22） |
| `doctor.py` | Owner（開工前、覺得怪怪的時候） | ✅ 已實作：環境健檢 + `claude -p` 冒煙測試與逾時診斷 + 五個驗證器 + 隔離層級 |

**約定**：被 Router 當作 `on_mention` 呼叫的程式，若判斷「這則訊息該交給 LLM 處理」就 `exit 3`。
