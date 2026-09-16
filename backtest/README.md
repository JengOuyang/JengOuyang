# backtest/ — 回測框架（LAB 的工作區）

| 檔案 | 職責 |
|---|---|
| `data_loader.py` | 8 年資料：Bitget 為主，T1 用 Binance 補、T3/T4 用現貨拼接並標註基差 |
| `engine.py` | 向量化回測（1H bar），成本模型：手續費、資金費率、滑價、止損下一根最差價 |
| `walkforward.py` | 6 段（訓練 16 個月／測試 8 個月）、±20% 參數擾動、Monte Carlo 1000 次 |
| `report.py` | 依 `shared/METRICS_SPEC.md` 產生 BACKTEST_REPORT |
| `reports/<change_id>/` | 產出：report.md、metrics.json、trades.csv、params.yaml |

鐵律：固定 seed 與資料版本，REDTEAM 必須能用 `--verify` 重跑出相同結果。禁止使用未來資料。
