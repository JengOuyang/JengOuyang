# engine/ — 核心程式 — 唯一碰錢與寫入資料的地方

**這些程式是確定性的，不含 LLM。** 規格在 `shared/`，由 FORGE 與 LAB 實作。

| 檔案 | 職責 | 規格出處 | 驗收標準 |
|---|---|---|---|
| `ingest_server.py` | LEDGER 的唯一寫入口：token 驗證、hash chain、寫 SQLite | `shared/DATA_SCHEMA.md` | `tests/test_hashchain.py` 通過；非法 token 被拒 |
| `risk_gate.py` | G1–G15 檢查、B 節倉位、C 節帳戶熔斷 | `shared/RISK_RULES.md` | `tests/test_risk_gate.py`：每條規則各一個通過與一個拒絕案例 |
| `executor.py` | Bitget 下單、10 秒止損檢查、棘輪、對帳、`!flatten` | `RISK_RULES.md` D/E 節 | DEMO 模式連跑 24h 無對帳差異 |
| `ratchet.py` | R0–R4 / RH 階段機 | `RISK_RULES.md` E 節 | SL 單調不回退 |
| `metrics.py` | 統一績效量尺（唯一計算入口） | `shared/METRICS_SPEC.md` | 回測與實盤用同一函式，數字可對帳 |
| `bitget_client.py` | ccxt 封裝：速率限制、重試、DEMO 切換、合約規格快取 | `skills/bitget-execution` | 斷線自動重連 |
| `marketing_metrics.py` | 行銷量尺 | `MARKETING_PLAYBOOK.md` §5 | — |

**改這裡任何檔案都要先 `!pause` 或確認在 DEMO 模式**，Router 每 5 分鐘會呼叫它們。
