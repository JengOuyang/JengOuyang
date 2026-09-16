---
name: task-management
description: CEO 立項、派工、追蹤、審核任務（tasks 表）時使用
---

# task-management

## 何時使用
CEO 立項、派工、追蹤、審核任務（tasks 表）時使用。

## 輸入 / 輸出契約
- **輸入**：Blacksheep 的需求或 Agent 的提案
- **輸出**：`TASK_ASSIGN` / `REVIEW_RESULT` + `tasks` 表一列
- **失敗時**：驗收標準寫不出可執行指令就代表任務定義不清，退回釐清而不是硬派

## 步驟
1. 用 scripts/task_db.py new 建立 task_id（T-YYYY-MMDD-NNN），填 title/description/acceptance_criteria[]/due/priority/assignee。
2. 發 TASK_ASSIGN 並 @ 負責 Agent（一次只給一個）。
3. 追蹤：30 分鐘無 ACK → 提醒；逾期 → 匯報列出。
4. 審核：逐條對照 acceptance_criteria 打分 1–5，寫 REVIEW_RESULT；不合格退回並說明。
5. 涉及金錢／規則／發佈 → 強制二審（REDTEAM/RISK/Owner）。

## 完成檢查
- [ ] 每個任務有 acceptance_criteria
- [ ] 審核在 24 小時內
- [ ] 決策寫入 decisions/

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/task_db.py（new/ack/progress/done/review/list）`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
