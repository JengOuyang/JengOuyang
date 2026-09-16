# 開發臨時筆記（TASKS.md）

> **建置待辦的唯一真相是 `../docs/08_BUILD_PLAN.md`。** CEO 從那裡取任務派給 FORGE，FORGE 完成後在那裡打勾。
> 這份檔案只放「你自己在 `dev/` 動手時」的臨時筆記，避免兩份待辦分岔。

## 我現在自己在做什麼
- [ ] （空）

## 動手前的檢查
- [ ] 已跟 CEO 說過（`!pause` 或在 `#human-inbox` 告知），避免撞到運行中的排程
- [ ] 確認 `strategy_params.yaml: mode: DEMO`（若要改 engine/）
- [ ] 若是大改動，用 git worktree 開獨立工作區

## 做完之後
- [ ] `python ../scripts/build_context.py`（若改過 `../shared/`）
- [ ] `python ../scripts/lint_agents.py`
- [ ] `python -m pytest ../tests -q`
- [ ] 在 `#human-inbox` 告訴 CEO 做了什麼，請它叫 FORGE 補測試與文件、並在 BUILD_PLAN 打勾

## 臨時想法（想到就記，之後請 CEO 立項）
-

## 變更提案

### PROPOSAL-20260916-01：CEO 每小時 LLM 呼叫上限 4 → 12
- **狀態**：✅ 已核准並套用——`CHG-2026-0916-001`，Blacksheep `!approve` 2026-09-16 20:21:22；strategy_params 2.0.1、tag `params-v1`。**待辦：`config_versions` 補登（apply_change.py 上線後）**
- **提出者**：Blacksheep（2026-09-16，dev session）
- **變更**：`shared/strategy_params.yaml` → `llm_budget.per_agent_hourly_calls.ceo: 4 → 12`
- **理由**：建置期 CEO 同時承接排程掃描、FORGE 回報與 Owner 決策回覆，2026-09-16 多次撞上 4 次上限，
  Owner 的回覆被延後 15 分鐘以上才處理。
- **風險**：CEO 例行用 sonnet，上限約為原本 3 倍；Pro 的 5 小時窗為全部 Agent 與開發 session 共用，
  CEO 屬 P1（額度吃緊時不讓路），會先擠壓 P2/P3。替代值：8。
- **不在本提案內**：延後時間 15 → 5 分鐘屬 Router 設定（`router/agents.yaml: budget_defer_minutes`），
  已於同日直接修改（非 Owner 核准參數）。
- **核准後的套用步驟**（`scripts/apply_change.py` 尚未實作，由 dev 手動代行）：
  1. 改數值；`version: 2.0.0 → 2.0.1`
  2. 同步 `agents/ceo/MANUAL.md`「每小時最多 4 次」
  3. `python scripts/build_context.py` → `/td-check`
  4. `docs/CHANGELOG.md` 記錄 change_id 與核准者
  5. `git tag params-v1`（對應 version 2.0.1）
  6. **待補登**：`config_versions` 一列（只能由 ingest 寫入口寫；待 `apply_change.py` 上線後補）
  7. 重啟 Router（`strategy_params.yaml` 於啟動時載入）
