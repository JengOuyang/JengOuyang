---
name: build-orchestration
description: CEO 在建置期把 docs/08_BUILD_PLAN.md 的待辦轉成可驗收的任務，派給 FORGE 或 LAB，追蹤並審核交付時使用
---

# build-orchestration

## 何時使用
系統尚未完工（`docs/08_BUILD_PLAN.md` 還有未打勾的項目）時，Blacksheep 要求推進建置進度。

## 輸入 / 輸出契約
- **輸入**：`docs/08_BUILD_PLAN.md` 的未完成項目
- **輸出**：`TASK_ASSIGN`（spec 指向 shared/ 節次、acceptance 為可執行指令）
- **失敗時**：項目描述不足以寫出可驗證的 acceptance → 先問 Blacksheep 釐清

## 步驟
1. 讀 `../../docs/08_BUILD_PLAN.md`，找出目前 Phase 中「未完成且無阻擋依賴」的項目。同時進行的 ≤ 2 項。
2. 每個項目寫成 `TASK_ASSIGN`，必要欄位：
   - `title`：動詞開頭，例如「實作 engine/risk_gate.py 的 G1–G15 檢查」
   - `spec`：**指向 `shared/` 的規格檔與節次**，例如 `shared/RISK_RULES.md § G, B`
   - `acceptance_criteria[]`：**每條都必須可機器驗證**，例如
     - `python -m pytest tests/test_risk_gate.py -q` 全數通過
     - `python scripts/lint_agents.py` 通過
     - G1–G15 每條規則各有一個通過與一個拒絕的測試案例
   - `assignee`：程式實作 → FORGE；回測框架 → LAB
   - `due`、`priority`
3. 在 `#forge`（或 `#backtest`）發出並 @ 該 Agent。
4. 追蹤：`TASK_ACK` 未在 30 分鐘內出現 → 提醒；`TASK_PROGRESS` 有 blockers → 記入日報。
5. 驗收 `TASK_DONE`：
   - 要求交付訊息附上 pytest 與 lint 的**實際輸出**，沒有就 `REJECTED`
   - 檢查是否符合引用的 `shared/` 規格
   - 涉及 `engine/executor.py`、`engine/risk_gate.py`、`engine/ingest_server.py` → 先 @REDTEAM 審，再 `HUMAN_DECISION_REQUIRED` 給 Blacksheep `!approve`
   - 通過 → `REVIEW_RESULT`（score 1–5）→ 請 FORGE 在 `docs/08_BUILD_PLAN.md` 打勾
6. 每日在 `#ceo-daily` 發建置日報（模板見 CEO 的 MANUAL.md）。

## 完成檢查
- [ ] 每個 acceptance_criteria 都能用一行指令驗證
- [ ] spec 指向 `shared/` 的具體節次，不是口語描述
- [ ] 同時進行的建置任務 ≤ 2
- [ ] 高風險交付（EXEC / RISK / LEDGER）走了 REDTEAM + Blacksheep 核准
- [ ] 完成的項目已在 BUILD_PLAN 打勾

## 相關程式
- `scripts/task_db.py`（任務板）
- `scripts/lint_agents.py`（驗收必跑）
