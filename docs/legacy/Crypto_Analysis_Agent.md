# 舊專案盤點：戰情室與行動端（`Crypto_Analysis_Agent`）

> 由 `python scripts/scan_legacy.py` 自動生成，**不要手改表格**——只有「決定」欄是給你填的。

- 路徑：`C:\Users\Ouyang\Desktop\My AI Agent\Crypto Analysis Agent`
- 狀態：production　信任度：medium
- 檔案數：623

## 已驗證的事實（CEO 派工時的優先依據）

- 每日盤面分析串接Canva
- 以DNN架構做盤面分析

## 踩過的坑（比程式本身更值錢——移植時必須保留這些處理）

- 無法直接推送Instegram
- 盤面分析不準確

## 依能力分類

### _未分類

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/m1_5_daily/model_manager.py` | 696 | __future__, datetime, json, logging, m1_5_daily | REF |
| `Crypto Analysis/m6_report/ig_publisher.py` | 570 | __future__, argparse, json, logging, os | REF |
| `Crypto Analysis/dev_sandboxvenv_py311/Scripts/Activate.ps1` | 503 | — | REF |
| `Crypto Analysis/dev_tool/sim/cycle_simulator.py` | 493 | __future__, dataclasses, datetime, dev_tool, json | REF |
| `Crypto Analysis/m2_analyzer/indicators.py` | 472 | __future__, math, numpy, typing | REF |
| `Crypto Analysis/dev_tool/stress/scenarios_p3c.py` | 402 | __future__, contextlib, datetime, dev_tool, numpy | REF |
| `Crypto Analysis/m5_backtest/_apply_calibration.py` | 398 | collections, m5_backtest, numpy, os, shared | REF |
| `Crypto Analysis/m1_5_daily/monthly_report.py` | 320 | __future__, argparse, calendar, datetime, json | REF |
| `Crypto Analysis/dev_tool/stress/scenarios.py` | 316 | __future__, dev_tool, typing | REF |
| `Crypto Analysis/m3_signals/confirmation_score.py` | 304 | __future__, dataclasses, shared | REF |
| `Crypto Analysis/run_daily.py` | 297 | __future__, argparse, datetime, json, m1_5_daily | REF |
| `Crypto Analysis/monitor/health_check.py` | 277 | argparse, data, datetime, json, logging | REF |
| `Crypto Analysis/m3_signals/funding_zscore.py` | 276 | __future__, argparse, dataclasses, m3_signals, numpy | REF |
| `Crypto Analysis/m3_5_dnn/features.py` | 270 | m2_analyzer, os, sys | REF |
| `Crypto Analysis/m3_signals/coinglass.py` | 266 | os, requests, time | REF |

### backtest-walkforward

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/backtest/results_20260430T045434Z.json` | 19534 | — | REF |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140146Z.json` | 19534 | — | REF |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140353Z.json` | 19390 | — | REF |
| `Crypto Analysis/m5_backtest/m4_backtest.py` | 1073 | argparse, collections, concurrent, datetime, json | REF |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140530Z.json` | 920 | — | REF |
| `Crypto Analysis/system_guide.html` | 904 | — | REF |
| `Crypto Analysis/m5_backtest/engine.py` | 794 | collections, datetime, m2_analyzer, numpy, os | REF |
| `Crypto Analysis/m5_backtest/train_m35.py` | 649 | argparse, data, datetime, json, m3_5_dnn | REF |
| `Crypto Analysis/m3_5_dnn/model.py` | 549 | features, logging, numpy, os, pickle | REF |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140401Z.json` | 487 | — | REF |
| `Crypto Analysis/m5_backtest/promotion_gate.py` | 409 | __future__, datetime, json, m5_backtest, numpy | REF |
| `Crypto Analysis/m5_backtest/collect_m4_training_data.py` | 376 | __future__, argparse, datetime, m3_5_dnn, m3_signals | REF |
| `Crypto Analysis/tests/test_e2e.py` | 353 | data, m1_5_daily, m3_5_dnn, m3_signals, m4_risk | REF |
| `Crypto Analysis/CLAUDE.md` | 346 | — | REF |
| `Crypto Analysis/dev_tool/tune/m4_lab.py` | 332 | __future__, copy, dataclasses, dev_tool, json | REF |

### data-integrity

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/system_guide.html` | 904 | — | REF |
| `Crypto Analysis/dev_tool/release/readiness.py` | 473 | __future__, dataclasses, datetime, dev_tool, json | REF |
| `Crypto Analysis/CLAUDE.md` | 346 | — | REF |
| `Crypto Analysis/shared/training_metadata.py` | 131 | __future__, datetime, hashlib, json, logging | REF |
| `Crypto Analysis/m3_5_dnn/weights/version_registry.json` | 98 | — | REF |
| `Crypto Analysis/m4_risk/weights/version_registry.json` | 87 | — | REF |
| `Crypto Analysis/m4_risk/weights/upgrade_log.json` | 56 | — | REF |
| `Crypto Analysis/m4_risk/weights/backups/champion_meta_pre13dim_20260605.json` | 44 | — | REF |
| `Crypto Analysis/m4_risk/weights/champion_meta.json` | 44 | — | REF |

### exchange-position-guard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/signals/pending.json` | 2572 | — | REF |
| `Crypto Analysis/m3_signals/signals.py` | 1332 | __future__, datetime, threading | REF |
| `Crypto Analysis/m6_report/canva_content.py` | 1313 | __future__, argparse, json, m4_risk, pathlib | REF |
| `Crypto Analysis/system_guide.html` | 904 | — | REF |
| `Crypto Analysis/m4_risk/engine.py` | 673 | collections, datetime, m4_risk, math, os | REF |
| `Crypto Analysis/run_pipeline.py` | 673 | __future__, argparse, data, datetime, json | REF |
| `Crypto Analysis/reports/daily_summary_2026-05-31.json` | 514 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-01.json` | 514 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-08-05.json` | 514 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-02.json` | 513 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-07.json` | 513 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-08.json` | 513 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-09.json` | 513 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-10.json` | 513 | — | REF |
| `Crypto Analysis/reports/daily_summary_2026-06-11.json` | 513 | — | REF |

### market-data-collection

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/m3_signals/signal_adapter.py` | 3660 | __future__, collections, os, shared, sys | REF |
| `Crypto Analysis/m5_backtest/m4_backtest.py` | 1073 | argparse, collections, concurrent, datetime, json | REF |
| `Crypto Analysis/system_guide.html` | 904 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260512_1600.json` | 897 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260512_1656.json` | 897 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260513_1314.json` | 897 | — | REF |
| `Crypto Analysis/m5_backtest/engine.py` | 794 | collections, datetime, m2_analyzer, numpy, os | REF |
| `Crypto Analysis/m1_5_daily/updater.py` | 741 | __future__, data, datetime, json, logging | REF |
| `Crypto Analysis/m3_5_dnn/signal_adapter.py` | 692 | __future__, datetime, json, logging, m3_5_dnn | REF |
| `Crypto Analysis/run_pipeline.py` | 673 | __future__, argparse, data, datetime, json | REF |
| `Crypto Analysis/shared/indicator_engine.py` | 654 | __future__, collections, m2_analyzer, m3_signals, numpy | REF |
| `Crypto Analysis/m5_backtest/train_m35.py` | 649 | argparse, data, datetime, json, m3_5_dnn | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260512_0354.json` | 645 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260512_0356.json` | 645 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/stress_run_20260512_0357.json` | 645 | — | REF |

### pattern-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/m3_signals/signal_adapter.py` | 3660 | __future__, collections, os, shared, sys | REF |
| `Crypto Analysis/shared/signal_schema.py` | 619 | __future__, dataclasses, math, typing | REF |
| `Crypto Analysis/m4_risk/signal_receiver.py` | 452 | __future__, logging, m4_risk, os, shared | REF |
| `Crypto Analysis/tests/test_e2e.py` | 353 | data, m1_5_daily, m3_5_dnn, m3_signals, m4_risk | REF |
| `Crypto Analysis/reports/report_20260602T185449_BTCUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260602T191810_BTCUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260603T091027_BNBUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260714T084230_ETHUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260730T094852_BNBUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260805T084253_BNBUSDT.html` | 120 | — | REF |

### smc-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/m3_signals/signal_adapter.py` | 3660 | __future__, collections, os, shared, sys | REF |
| `Crypto Analysis/m3_signals/signals.py` | 1332 | __future__, datetime, threading | REF |
| `Crypto Analysis/m5_backtest/m4_backtest.py` | 1073 | argparse, collections, concurrent, datetime, json | REF |
| `Crypto Analysis/run_pipeline.py` | 673 | __future__, argparse, data, datetime, json | REF |
| `Crypto Analysis/m5_backtest/train_m35.py` | 649 | argparse, data, datetime, json, m3_5_dnn | REF |
| `Crypto Analysis/shared/signal_schema.py` | 619 | __future__, dataclasses, math, typing | REF |
| `Crypto Analysis/m4_risk/signal_receiver.py` | 452 | __future__, logging, m4_risk, os, shared | REF |
| `Crypto Analysis/m5_backtest/_tiered_signal_system.py` | 452 | collections, datetime, itertools, m3_signals, m5_backtest | REF |
| `Crypto Analysis/m4_risk/fusion/xgb_fusion.py` | 399 | __future__, m4_risk, numpy, os, pickle | REF |
| `Crypto Analysis/tests/test_e2e.py` | 353 | data, m1_5_daily, m3_5_dnn, m3_signals, m4_risk | REF |
| `Crypto Analysis/m5_backtest/compare_m3_vs_m35.py` | 314 | argparse, m3_5_dnn, m5_backtest, numpy, os | REF |
| `Crypto Analysis/m5_backtest/_signal_calibration.py` | 192 | collections, datetime, m5_backtest, numpy, os | REF |
| `Crypto Analysis/reports/report_20260601T205859_ETHUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260601T210136_ETHUSDT.html` | 124 | — | REF |
| `Crypto Analysis/reports/report_20260601T210137_SOLUSDT.html` | 124 | — | REF |

### war-room-dashboard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/CLAUDE.md` | 346 | — | REF |
| `Crypto Analysis/dev_sandbox/reports/py314_incompat_diagnostic.md` | 72 | — | REF |
