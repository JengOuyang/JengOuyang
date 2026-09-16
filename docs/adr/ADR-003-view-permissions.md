# ADR-003：資料存取權限做在視圖層，而非 prompt 約束

狀態：**採納** · 日期 2026-09-09

## 背景
Agent 需要查資料倉，但有些資料不該給某些 Agent：REDTEAM 看到 CHART 的推理就不是盲審；CREATIVE 拿到進場價可能在 IG 洩漏；CHART 看到 Gate 門檻會優化通過率而非交易品質。

## 選項
| 方案 | 強度 |
|---|---|
| A. 在 PERSONA.md 寫「你不要查 X」 | 勸告，模型可能忽略，且無稽核 |
| B. 每個 Agent 一個資料庫副本 | 隔離強但資料會不同步、磁碟翻倍 |
| C. 視圖層裁切 + 授權矩陣強制 | 物理隔離、單一資料源、可稽核 |

## 決定
選 **C**：
- `db/002_views.sql` 定義 44 個視圖，欄位裁切在 SQL 完成（例如 `v_blind_plan` 用 `json_remove` 剔除 `reasoning` 與 `confidence`）。
- `shared/view_grants.yaml` 定義誰能查哪些視圖。
- `scripts/query_readonly.py` 在執行前解析 SQL 的 FROM/JOIN，未授權即拒絕；**完全禁止查底層資料表**。
- `lint_agents.py` 交叉檢查授權的視圖都有定義。

## 後果
- 新增查詢需求要先新增視圖與授權（走 SKILL_REQUEST → FORGE）。這個摩擦是刻意的。
- `query_readonly.py` 的 SQL 解析是正則，不是完整 parser——它是縱深防禦的一層，不是唯一一層（連線本身也是 `mode=ro` + `query_only`）。

## 何時重新考慮
若改用 PostgreSQL，可直接用資料庫的 ROLE/GRANT 取代自寫檢查。
