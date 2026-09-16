---
name: llm-budget
description: 估算與管理 Claude Pro 用量（5 小時窗、週窗）
---

# llm-budget

## 何時使用
估算與管理 Claude Pro 用量（5 小時窗、週窗）。

## 輸入 / 輸出契約
- **輸入**：`router_state.db` 的 calls 表 + Pro 方案窗口
- **輸出**：`{window_used_pct, per_agent_calls, action}`（估計值須標註）
- **失敗時**：無法取得用量 → 保守假設已用 80% 並通知，不要假設還很多

## 步驟
1. 累計 Router 記錄的 llm_usage（tokens、次數、模型）。
2. 剩 20% 預警；剩 10% 通知 Router 延後 defer_agents_when_low。
3. !budget 回覆各 Agent 今日呼叫數與估計占比（標註為估計）。

## 完成檢查
- [ ] 估計值標註

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/usage.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
