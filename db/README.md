# db/ — 資料庫結構定義

| 檔案 | 內容 |
|---|---|
| `001_schema.sql` | 31 個表：行情、分析、執行、稽核、行銷、維運。全部 append-only + hash chain 欄位 |
| `002_views.sql` | 41 個視圖 = **權限層**。欄位裁切在這裡完成（例如 `v_blind_plan` 剔除 CHART 的 reasoning） |
| `migrations/` | 之後的變更，命名 `003_xxx.sql`，`init_db.py` 會依序套用 |

建庫：`python scripts/init_db.py`（可重複執行）。
改視圖後要同步更新 `shared/view_grants.yaml`，`lint_agents.py` 會交叉檢查。
