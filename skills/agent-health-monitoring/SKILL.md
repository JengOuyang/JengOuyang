---
name: agent-health-monitoring
description: WATCH 心跳、狀態燈、告警、Dashboard
---

# agent-health-monitoring

## 何時使用
WATCH 心跳、狀態燈、告警、Dashboard。

## 輸入 / 輸出契約
- **輸入**：`agent_heartbeat` + 各 Agent 的預期週期
- **輸出**：`{agent_id, light: 綠/黃/紅, last_seen, suggested_action}`
- **失敗時**：EXEC 10 分鐘無心跳 → 觸發 Kill Switch 檢查流程，不只是告警

## 步驟
1. 讀 agent_heartbeat；依預期週期算綠／黃／紅。
2. EXEC 10 分鐘無心跳 → Kill Switch 檢查。
3. 告警含建議動作。

## 完成檢查
- [ ] 告警可行動

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/heartbeat_check.py`
- `dashboard/app.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
