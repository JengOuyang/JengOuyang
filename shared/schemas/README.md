# shared/schemas/ — 結構化輸出的 JSON Schema

Agent 的產出必須通過對應 schema 驗證才會被下游接受。程式用 `jsonschema` 套件檢查。

| 檔案 | 誰產出 | 誰驗證 |
|---|---|---|
| `trade_plan.schema.json` | CHART | `engine/risk_gate.py` |
| `trade_journal.schema.json` | AUDIT | `scripts/write_review.py` |
| `macro_brief.schema.json` | MACRO | `scripts/write_macro.py` |
| `risk_decision.schema.json` | RISK（程式） | `engine/executor.py` |
| `content_draft.schema.json` | CREATIVE | `scripts/publisher.py` |
| `message.schema.json` | 全體 | Router（訊息信封格式） |
