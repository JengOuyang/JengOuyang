## 這個變更改了什麼

<!-- 一句話。若是 FORGE 產出的修復，貼上 merge_fix.py 的報告 -->

## 影響哪一層

- [ ] 思考層（Agent 手冊 / Persona / 切片）
- [ ] 閘門層（RISK_RULES / Risk Gate / 參數）← 需要 Blacksheep `!approve`
- [ ] 執行層（engine / router / 下單路徑）← 需要 REDTEAM 覆核
- [ ] 資料層（db schema / 視圖 / 授權矩陣）

## 檢查

- [ ] `python scripts/lint_agents.py` 通過
- [ ] `python scripts/verify_isolation.py` 通過
- [ ] `python -m pytest -q` 通過
- [ ] 沒有動到 `shared/`（動 shared 必須走 RISK_RULES H 節流程，不能用 PR）
- [ ] 沒有新增金鑰、沒有放寬任何 Agent 的寫入範圍
