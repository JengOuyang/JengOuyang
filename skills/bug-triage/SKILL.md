---
name: bug-triage
description: FORGE 收到 BUG_REPORT 或 Router 的 ❌ 時，重現問題並歸因到具體的 skill 或程式
---

# bug-triage

## 何時使用
有東西壞了，但還不知道是哪一層壞的。**先歸因再修，不要直接改**。

## 輸入 / 輸出契約
- **輸入**：BUG_REPORT 或 Router 自動產生的失敗紀錄
- **輸出**：`{bug_id, skill_name, root_cause_hypothesis, repro_steps, severity, recurring: bool}`
- **失敗時**：無法重現就誠實標 `NOT_REPRODUCIBLE` 並列出需要的額外資訊，不要臆測修改

## 步驟
1. 讀 BUG_REPORT 的 repro_steps 與 `logs/router.log` 對應時間區間。
2. 重現：能重現就記下最小重現步驟；不能重現就記下觀察到的現象與差異假設，不要硬修。
3. 歸因到**最小的失敗單位**：哪一個 skill、哪一支程式、哪一行。填入 `bug_reports.skill_name`。
4. 分級：P0（碰錢或資料完整性）/ P1（阻擋交易流程）/ P2（單一 Agent 功能）/ P3（體驗）。
5. 查 `v_skill_failures`：這個 skill 是不是重複出事？重複三次以上代表是設計問題不是實作問題，要提架構修改而不是補丁。

## 完成檢查
- [ ] 歸因到 skill 層級不只是 agent
- [ ] 有最小重現步驟或明確的「無法重現」
- [ ] 查過是否為重複故障

## 相關程式
- `scripts/lint_agents.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
