---
name: change-review
description: CEO 或 REDTEAM 審核 FORGE / LAB 的交付，決定是否合併時使用
---

# change-review

## 何時使用
收到 FIX_PROPOSAL 或 TASK_DONE，要決定接受、退回或升級。

## 輸入 / 輸出契約
- **輸入**：FIX_PROPOSAL 或 TASK_DONE + 對應的 acceptance_criteria
- **輸出**：`REVIEW_RESULT{verdict, score, per_criterion[], independent_verification}`
- **失敗時**：驗證程式本身跑不起來 → 視同 FAIL，先修驗證環境

## 步驟
1. **自己跑 `python ../../scripts/verify_delivery.py --task <id> --tests <...> --files <...>`**——不要相信交付者貼上來的測試輸出。
2. 逐條對照 `acceptance_criteria`，每條標 PASS / FAIL 並附證據。
3. 判斷風險層級：碰到 `engine/executor.py`、`engine/risk_gate.py`、`engine/ingest_server.py` → 必須 @REDTEAM 審行為是否改變，再 `HUMAN_DECISION_REQUIRED` 請 Blacksheep 核准。
4. EXEC 相關的改動先在 DEMO 跑 24 小時才可合併到 LIVE 分支。
5. 通過 → `REVIEW_RESULT`（score 1–5 + 理由）；不通過 → `REJECTED` + 具體缺什麼。
6. 合併後請交付者在 `docs/08_BUILD_PLAN.md` 打勾並在 `#forge` 公告。

## 完成檢查
- [ ] 驗證是自己跑的不是引用對方的
- [ ] 每條 acceptance 都有裁決
- [ ] 高風險改動走了 REDTEAM + Blacksheep

## 相關程式
- `scripts/verify_delivery.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
