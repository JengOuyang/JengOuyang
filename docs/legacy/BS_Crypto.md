# 舊專案盤點：量化交易主專案（`BS_Crypto`）

> 由 `python scripts/scan_legacy.py` 自動生成，**不要手改表格**——只有「決定」欄是給你填的。

- 路徑：`C:\Users\Ouyang\Desktop\My AI Agent\BS Crypto`
- 狀態：production　信任度：high
- 檔案數：3030

## 已驗證的事實（CEO 派工時的優先依據）

- 策略通過 2 個月 Gate A（實盤／模擬盤樣本）
- Bitget 下單與部位查詢連續運行未中斷

## 踩過的坑（比程式本身更值錢——移植時必須保留這些處理）

- 資金費率結算時間點的處理曾出錯
- 交易所限流在高波動時會觸發
- 市場變化時策略無法及時因應變化做反應(無法保持每日持續正獲利)

## ⚠️ 含疑似金鑰的檔案（移植前必須先清掉，並在交易所端輪換）

- `server/config.py`

## 依能力分類

### _未分類

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `cto/m1_5_daily/model_manager.py` | 731 | __future__, cto, datetime, json, logging | |
| `tests/test_exp01a_engine.py` | 641 | copy, cro, inspect, json, os | |
| `cto/m3_signals/signal_adapter/rules/oscillators.py` | 608 | __future__, build, shared | |
| `cfo/m6_report/ig_publisher.py` | 570 | __future__, argparse, json, logging, os | |
| `server/base.py` | 530 | abc, asyncio, dataclasses, datetime, httpx | |
| `research/scripts/sim/cycle_simulator.py` | 493 | __future__, dataclasses, datetime, dev_tool, json | |
| `cto/m3_signals/signal_adapter/rules/candles.py` | 489 | __future__, build, shared | |
| `cmo/channel_engine.py` | 487 | __future__, cmo, json, os, re | |
| `tests/test_exp01f_engine_extensions.py` | 466 | cro, dataclasses, json, pathlib, pytest | |
| `frontend/app/operations/page.tsx` | 440 | @/components/ui/badge, @/components/ui/card, @/lib/apiBase, @/lib/types, react | |
| `coo/agent.py` | 439 | data, datetime, json, logging, pathlib | |
| `cto/agent.py` | 430 | datetime, httpx, json, logging, numpy | |
| `cmo/channel_intel.py` | 420 | __future__, asyncio, cmo, datetime, json | |
| `cmo/extract_node_material.py` | 416 | __future__, argparse, dataclasses, difflib, json | |
| `cto/m3_signals/signal_adapter/rules/htf_trend.py` | 407 | __future__, build, shared | |

### backtest-walkforward

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `cto/backtest/results_20260430T045434Z.json` | 19534 | — | |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | |
| `cto/system_guide.html` | 904 | — | |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | |
| `cto/m5_backtest/engine.py` | 882 | collections, cto, datetime, numpy, os | |
| `docs/design/technical_spec.md` | 775 | — | |
| `docs/collab/CURRENT_STATE.md` | 748 | — | |
| `cto/m5_backtest/train_m35.py` | 674 | argparse, cto, data, datetime, json | |
| `research/scripts/deflated_sharpe_pbo.py` | 611 | __future__, math, numpy | |
| `research/scripts/exp03b_preq.py` | 578 | __future__, argparse, contextlib, cro, dataclasses | |
| `cto/m3_5_dnn/model.py` | 568 | features, numpy, os, pickle, torch | |

### data-integrity

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `research/outputs/exp03b_v3_1_fills/tiabtc_atr.json` | 44792 | — | |
| `research/outputs/exp03b_v3_fills/tiabtc_atr.json` | 42720 | — | |
| `research/outputs/exp03b_v3_2_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_4_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_5_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_1_fills/tiabtc_struct.json` | 30666 | — | |
| `research/outputs/exp03b_v3_fills/tiabtc_struct.json` | 29182 | — | |
| `research/outputs/exp03b_fills_v1/xiaom924_atr.json` | 13646 | — | |
| `research/outputs/exp03b_fills_v2/xiaom924_atr.json` | 13387 | — | |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `research/outputs/exp03b_fills_v2/xiaom924_struct.json` | 10003 | — | |
| `research/outputs/exp03b_fills_v1/tiabtc_atr.json` | 8978 | — | |
| `research/outputs/exp03b_fills_v1/xiaom924_struct.json` | 8762 | — | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `research/outputs/exp03b_fills_v1/tiabtc_struct.json` | 6458 | — | |

### exchange-order-placement

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `cro/trader.py` | 462 | asyncio, base64, datetime, hashlib, hmac | |
| `tests/test_trader_idempotency.py` | 451 | asyncio, cro, os, pytest, unittest | |
| `ciso/api/settings.py` | 351 | base64, fastapi, getpass, hashlib, hmac | |
| `server/client.py` | 237 | asyncio, base64, datetime, hashlib, hmac | |
| `shared/multi_funding.py` | 166 | __future__, numpy, pathlib, requests, shared | |
| `research/scripts/exec_cost_calibration.py` | 104 | cro, numpy, os, requests, shared | |
| `docs/design/carry_phase2_plan.md` | 72 | — | |
| `research/scripts/carry_universe_filter.py` | 65 | os, requests, shared, sys, time | |
| `scripts/record_flow.py` | 53 | json, os, shared, sys, time | |
| `cro/market_data.py` | 42 | httpx, logging, server, shared | |

### exchange-position-guard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `cro/signals/pending.json` | 14702 | — | |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `cto/m3_signals/signals.py` | 1332 | __future__, datetime, threading | |
| `cfo/m6_report/canva_content.py` | 1314 | __future__, argparse, cto, json, pathlib | |
| `cto/system_guide.html` | 904 | — | |
| `frontend/app/page.tsx` | 903 | @/hooks/useWarroomStream, @/lib/apiBase, @/lib/apiFetch, @/lib/types, next/link | |
| `coo/run_pipeline.py` | 790 | __future__, argparse, asyncio, cfo, cto | |
| `docs/design/technical_spec.md` | 775 | — | |
| `frontend/app/pnl/page.tsx` | 735 | @/components/ui/badge, @/components/ui/card, @/contexts/PnlContext, @/lib/apiBase, @/lib/apiFetch | |
| `cro/agent.py` | 631 | cro, datetime, json, logging, os | |
| `cto/m4_risk/engine.py` | 573 | collections, cto, os, shared, sys | |
| `research/outputs/daily_summary_2026-05-31.json` | 514 | — | |

### exchange-reconciliation

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `frontend/app/page.tsx` | 903 | @/hooks/useWarroomStream, @/lib/apiBase, @/lib/apiFetch, @/lib/types, next/link | |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | |
| `docs/design/exp01d_crypto_punks_bindings.md` | 872 | — | |
| `docs/collab/CURRENT_STATE.md` | 748 | — | |
| `shared/backtest_kit.py` | 648 | __future__, collections, dataclasses, hashlib, json | |
| `cro/agent.py` | 631 | cro, datetime, json, logging, os | |
| `ceo/agent.py` | 529 | datetime, json, logging, re, server | |
| `docs/design/backtest_nav_methodology.md` | 482 | — | |
| `coo/agent_runner.py` | 481 | asyncio, ceo, cfo, ciso, cmo | |
| `docs/collab/task_registry.md` | 471 | — | |
| `tests/test_cro_orders.py` | 416 | cro, json, os, pytest, server | |

### macro-briefing

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `frontend/package-lock.json` | 9926 | — | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `cmo/intel/crypto_punks/meta.json` | 957 | — | |
| `tests/test_exp01e_tiabtc.py` | 912 | ast, coo, cro, datetime, hashlib | |
| `cmo/intel/giantcutie-k/meta.json` | 823 | — | |
| `docs/design/exp01d_crypto_punks_material.md` | 587 | — | |
| `docs/design/intel02_data_manifest.md` | 557 | — | |
| `cmo/intel/giantcutie-k/intel_tree.json` | 522 | — | |
| `docs/design/exp01c_giantcutie_material.md` | 500 | — | |
| `docs/design/intel02_source_registry.md` | 313 | — | |
| `cmo/intel/giantcutie-k/intel_tree_v1.json` | 294 | — | |
| `cmo/intel/xiaom924/meta.json` | 236 | — | |
| `cmo/intel/giantcutie-k/intel_tree.md` | 141 | — | |
| `cmo/intel/giantcutie-k/intel_tree_v1.md` | 116 | — | |
| `cmo/intel/giantcutie-k/batches/batch_006.md` | 62 | — | |

### market-data-collection

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | |
| `cro/expert/detectors/tiabtc.py` | 1346 | __future__, cro, shared, typing | |
| `cro/expert/trees/giantcutie.json` | 1203 | — | |
| `research/outputs/exp_va_cognitive_verification.md` | 1184 | — | |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | |
| `tests/test_exp01c_giantcutie.py` | 1039 | ast, cro, inspect, json, pathlib | |
| `shared/indicator_engine.py` | 1013 | __future__, collections, cto, numpy, os | |
| `docs/design/exp01e_tiabtc_bindings.md` | 1007 | — | |
| `cmo/intel/crypto_punks/meta.json` | 957 | — | |

### pattern-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | |
| `cro/expert/detectors/tiabtc.py` | 1346 | __future__, cro, shared, typing | |
| `research/outputs/exp_va_cognitive_verification.md` | 1184 | — | |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | |
| `tests/test_structure.py` | 1056 | cro, inspect, pytest, shared | |
| `docs/design/exp01e_tiabtc_bindings.md` | 1007 | — | |
| `tests/test_exp01d_crypto_punks.py` | 920 | ast, cro, hashlib, inspect, json | |
| `cro/expert/trees/crypto_punks.json` | 910 | — | |
| `docs/design/exp01d_crypto_punks_bindings.md` | 872 | — | |
| `docs/collab/CURRENT_STATE.md` | 748 | — | |
| `cto/m3_signals/signal_adapter/rules/chart_patterns.py` | 678 | __future__, build, shared | |

### ratchet-management

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `research/outputs/exp03b_v3_2_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_4_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_5_fills/tiabtc_struct.json` | 32856 | — | |
| `research/outputs/exp03b_v3_1_fills/tiabtc_struct.json` | 30666 | — | |
| `research/outputs/exp03b_v3_fills/tiabtc_struct.json` | 29182 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | |
| `shared/backtest_kit.py` | 648 | __future__, collections, dataclasses, hashlib, json | |
| `research/scripts/exp03b_preq.py` | 578 | __future__, argparse, contextlib, cro, dataclasses | |
| `docs/collab/task_registry.md` | 471 | — | |
| `research/outputs/exp_gate1_material.md` | 402 | — | |
| `research/scripts/exp_regime_stratify.py` | 283 | __future__, collections, cro, datetime, json | |
| `research/harness.py` | 272 | __future__, cro, datetime, numpy, os | |
| `tests/test_pa_paper.py` | 240 | cro, json, pytest | |
| `tests/test_swing_paper.py` | 223 | cro, json, numpy, pytest, shared | |

### smc-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `frontend/package-lock.json` | 9926 | — | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | |
| `cto/m3_signals/signals.py` | 1332 | __future__, datetime, threading | |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | |
| `tests/test_structure.py` | 1056 | cro, inspect, pytest, shared | |
| `tests/test_exp01c_giantcutie.py` | 1039 | ast, cro, inspect, json, pathlib | |
| `coo/run_pipeline.py` | 790 | __future__, argparse, asyncio, cfo, cto | |
| `cto/m5_backtest/train_m35.py` | 674 | argparse, cto, data, datetime, json | |
| `cro/expert/detectors/xiaom924.py` | 646 | __future__, cro, shared | |
| `tests/test_exp01b_xiaom924.py` | 633 | cro, json, pathlib, pytest, re | |

### war-room-dashboard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | |
| `frontend/app/pnl/page.tsx` | 735 | @/components/ui/badge, @/components/ui/card, @/contexts/PnlContext, @/lib/apiBase, @/lib/apiFetch | |
| `docs/collab/task_registry.md` | 471 | — | |
| `CLAUDE.md` | 449 | — | |
| `server/ws.py` | 408 | asyncio, ceo, coo, cro, datetime | |
| `docs/crypto_agent_ref/CLAUDE_original.md` | 346 | — | |
| `docs/design/dashboard_pages.md` | 328 | — | |
| `.claude/settings.local.json` | 280 | — | |
| `docs/collab/health_remediation_plan.md` | 253 | — | |
| `coo/api/operations.py` | 240 | datetime, fastapi, json, logging, server | |
| `server/main.py` | 224 | asyncio, ceo, cfo, ciso, cmo | |
| `docs/design/org_charter.md` | 204 | — | |
