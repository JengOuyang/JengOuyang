# tests/ — 單元測試與整合測試

`python -m pytest tests -q`

優先要有的測試：
| 檔案 | 驗什麼 |
|---|---|
| `test_hashchain.py` | 竄改任一列後 `verify_chain.py` 會失敗 |
| `test_risk_gate.py` | G1–G15 每條規則各一個通過 + 一個拒絕案例；倉位算式邊界 |
| `test_ratchet.py` | SL 單調不回退；R1–R4 階段轉換 |
| `test_view_grants.py` | 每個 Agent 查未授權視圖會被拒 |
| `test_build_context.py` | 改 shared/ 後 `--verify` 會失敗；重建後通過 |
| `test_schemas.py` | 範例 TradePlan / TradeReview 通過 schema |

提交前必跑：`python scripts/lint_agents.py && python -m pytest tests -q`
