---
name: fix-and-verify
description: FORGE 依據 bug-triage 的歸因實作修復並自我驗證時使用
---

# fix-and-verify

## 何時使用
已知道哪裡壞了，要動手修。

## 輸入 / 輸出契約
- **輸入**：bug-triage 的歸因結果
- **輸出**：`FIX_PROPOSAL{bug_id, skill_name, root_cause, diff_summary, files, tests_run, verify_delivery_output, risk_level, rollback}`
- **失敗時**：修不好就回報阻礙與已排除的假設，不要交出沒把握的程式

## 步驟
1. 開分支 `fix/<bug_id>`（高風險改動用 `git worktree` 開獨立工作區，避免影響運行中的系統）。
2. **先寫一個會失敗的測試**，再修到它通過。沒有測試的修復不算修復。
3. 最小改動原則：只碰造成問題的那一段，不順手重構。
4. 跑 `pytest` + `python scripts/lint_agents.py` + `build_context.py --verify`。
5. 改到 `shared/` 就必須重跑 `build_context.py`，否則 Agent 會停工。
6. 產出 `FIX_PROPOSAL`，附上 `scripts/verify_delivery.py` 的**完整輸出**——你自己說「測試通過」不算證據。

## 完成檢查
- [ ] 有一個新測試涵蓋這個 bug
- [ ] verify_delivery 輸出為 PASS
- [ ] 有 rollback 指令
- [ ] 改 shared/ 後重建過切片

## 相關程式
- `scripts/verify_delivery.py`
- `scripts/build_context.py`
- `scripts/lint_agents.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
