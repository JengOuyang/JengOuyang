# db/migrations/ — 資料庫變更

命名 `003_描述.sql` 起跳，只新增不修改既有檔案。每個 migration 必須可重複執行（`IF NOT EXISTS` / `INSERT OR IGNORE`）。

schema 變更流程：FORGE 提案 → LEDGER 審（是否破壞 hash chain 或既有視圖）→ 合併 → `python scripts/init_db.py`。
