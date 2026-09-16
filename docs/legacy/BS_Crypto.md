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
| `cto/m1_5_daily/model_manager.py` | 731 | __future__, cto, datetime, json, logging | REF |
| `tests/test_exp01a_engine.py` | 641 | copy, cro, inspect, json, os | REF |
| `cto/m3_signals/signal_adapter/rules/oscillators.py` | 608 | __future__, build, shared | REF |
| `cfo/m6_report/ig_publisher.py` | 570 | __future__, argparse, json, logging, os | REF |
| `server/base.py` | 530 | abc, asyncio, dataclasses, datetime, httpx | REF |
| `research/scripts/sim/cycle_simulator.py` | 493 | __future__, dataclasses, datetime, dev_tool, json | REF |
| `cto/m3_signals/signal_adapter/rules/candles.py` | 489 | __future__, build, shared | REF |
| `cmo/channel_engine.py` | 487 | __future__, cmo, json, os, re | REF |
| `tests/test_exp01f_engine_extensions.py` | 466 | cro, dataclasses, json, pathlib, pytest | REF |
| `frontend/app/operations/page.tsx` | 440 | @/components/ui/badge, @/components/ui/card, @/lib/apiBase, @/lib/types, react | REF |
| `coo/agent.py` | 439 | data, datetime, json, logging, pathlib | REF |
| `cto/agent.py` | 430 | datetime, httpx, json, logging, numpy | REF |
| `cmo/channel_intel.py` | 420 | __future__, asyncio, cmo, datetime, json | REF |
| `cmo/extract_node_material.py` | 416 | __future__, argparse, dataclasses, difflib, json | REF |
| `cto/m3_signals/signal_adapter/rules/htf_trend.py` | 407 | __future__, build, shared | REF |

### backtest-walkforward

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `cto/backtest/results_20260430T045434Z.json` | 19534 | — | REF |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | REF |
| `cto/system_guide.html` | 904 | — | REF |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | REF |
| `cto/m5_backtest/engine.py` | 882 | collections, cto, datetime, numpy, os | REF |
| `docs/design/technical_spec.md` | 775 | — | REF |
| `docs/collab/CURRENT_STATE.md` | 748 | — | REF |
| `cto/m5_backtest/train_m35.py` | 674 | argparse, cto, data, datetime, json | REF |
| `research/scripts/deflated_sharpe_pbo.py` | 611 | __future__, math, numpy | REF |
| `research/scripts/exp03b_preq.py` | 578 | __future__, argparse, contextlib, cro, dataclasses | REF |
| `cto/m3_5_dnn/model.py` | 568 | features, numpy, os, pickle, torch | REF |

### data-integrity

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `research/outputs/exp03b_v3_1_fills/tiabtc_atr.json` | 44792 | — | REF |
| `research/outputs/exp03b_v3_fills/tiabtc_atr.json` | 42720 | — | REF |
| `research/outputs/exp03b_v3_2_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_4_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_5_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_1_fills/tiabtc_struct.json` | 30666 | — | REF |
| `research/outputs/exp03b_v3_fills/tiabtc_struct.json` | 29182 | — | REF |
| `research/outputs/exp03b_fills_v1/xiaom924_atr.json` | 13646 | — | REF |
| `research/outputs/exp03b_fills_v2/xiaom924_atr.json` | 13387 | — | REF |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `research/outputs/exp03b_fills_v2/xiaom924_struct.json` | 10003 | — | REF |
| `research/outputs/exp03b_fills_v1/tiabtc_atr.json` | 8978 | — | REF |
| `research/outputs/exp03b_fills_v1/xiaom924_struct.json` | 8762 | — | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `research/outputs/exp03b_fills_v1/tiabtc_struct.json` | 6458 | — | REF |

### exchange-order-placement

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `cro/trader.py` | 462 | asyncio, base64, datetime, hashlib, hmac | REF |
| `tests/test_trader_idempotency.py` | 451 | asyncio, cro, os, pytest, unittest | REF |
| `ciso/api/settings.py` | 351 | base64, fastapi, getpass, hashlib, hmac | REF |
| `server/client.py` | 237 | asyncio, base64, datetime, hashlib, hmac | REF |
| `shared/multi_funding.py` | 166 | __future__, numpy, pathlib, requests, shared | REF |
| `research/scripts/exec_cost_calibration.py` | 104 | cro, numpy, os, requests, shared | REF |
| `docs/design/carry_phase2_plan.md` | 72 | — | REF |
| `research/scripts/carry_universe_filter.py` | 65 | os, requests, shared, sys, time | REF |
| `scripts/record_flow.py` | 53 | json, os, shared, sys, time | REF |
| `cro/market_data.py` | 42 | httpx, logging, server, shared | REF |

### exchange-position-guard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `cro/signals/pending.json` | 14702 | — | REF |
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `cto/m3_signals/signals.py` | 1332 | __future__, datetime, threading | REF |
| `cfo/m6_report/canva_content.py` | 1314 | __future__, argparse, cto, json, pathlib | REF |
| `cto/system_guide.html` | 904 | — | REF |
| `frontend/app/page.tsx` | 903 | @/hooks/useWarroomStream, @/lib/apiBase, @/lib/apiFetch, @/lib/types, next/link | REF |
| `coo/run_pipeline.py` | 790 | __future__, argparse, asyncio, cfo, cto | REF |
| `docs/design/technical_spec.md` | 775 | — | REF |
| `frontend/app/pnl/page.tsx` | 735 | @/components/ui/badge, @/components/ui/card, @/contexts/PnlContext, @/lib/apiBase, @/lib/apiFetch | REF |
| `cro/agent.py` | 631 | cro, datetime, json, logging, os | REF |
| `cto/m4_risk/engine.py` | 573 | collections, cto, os, shared, sys | REF |
| `research/outputs/daily_summary_2026-05-31.json` | 514 | — | REF |

### exchange-reconciliation

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `frontend/app/page.tsx` | 903 | @/hooks/useWarroomStream, @/lib/apiBase, @/lib/apiFetch, @/lib/types, next/link | REF |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | REF |
| `docs/design/exp01d_crypto_punks_bindings.md` | 872 | — | REF |
| `docs/collab/CURRENT_STATE.md` | 748 | — | REF |
| `shared/backtest_kit.py` | 648 | __future__, collections, dataclasses, hashlib, json | REF |
| `cro/agent.py` | 631 | cro, datetime, json, logging, os | REF |
| `ceo/agent.py` | 529 | datetime, json, logging, re, server | REF |
| `docs/design/backtest_nav_methodology.md` | 482 | — | REF |
| `coo/agent_runner.py` | 481 | asyncio, ceo, cfo, ciso, cmo | REF |
| `docs/collab/task_registry.md` | 471 | — | REF |
| `tests/test_cro_orders.py` | 416 | cro, json, os, pytest, server | REF |

### macro-briefing

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `frontend/package-lock.json` | 9926 | — | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `cmo/intel/crypto_punks/meta.json` | 957 | — | REF |
| `tests/test_exp01e_tiabtc.py` | 912 | ast, coo, cro, datetime, hashlib | REF |
| `cmo/intel/giantcutie-k/meta.json` | 823 | — | REF |
| `docs/design/exp01d_crypto_punks_material.md` | 587 | — | REF |
| `docs/design/intel02_data_manifest.md` | 557 | — | REF |
| `cmo/intel/giantcutie-k/intel_tree.json` | 522 | — | REF |
| `docs/design/exp01c_giantcutie_material.md` | 500 | — | REF |
| `docs/design/intel02_source_registry.md` | 313 | — | REF |
| `cmo/intel/giantcutie-k/intel_tree_v1.json` | 294 | — | REF |
| `cmo/intel/xiaom924/meta.json` | 236 | — | REF |
| `cmo/intel/giantcutie-k/intel_tree.md` | 141 | — | REF |
| `cmo/intel/giantcutie-k/intel_tree_v1.md` | 116 | — | REF |
| `cmo/intel/giantcutie-k/batches/batch_006.md` | 62 | — | REF |

### market-data-collection

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | REF |
| `cro/expert/detectors/tiabtc.py` | 1346 | __future__, cro, shared, typing | REF |
| `cro/expert/trees/giantcutie.json` | 1203 | — | REF |
| `research/outputs/exp_va_cognitive_verification.md` | 1184 | — | REF |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | REF |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | REF |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | REF |
| `tests/test_exp01c_giantcutie.py` | 1039 | ast, cro, inspect, json, pathlib | REF |
| `shared/indicator_engine.py` | 1013 | __future__, collections, cto, numpy, os | REF |
| `docs/design/exp01e_tiabtc_bindings.md` | 1007 | — | REF |
| `cmo/intel/crypto_punks/meta.json` | 957 | — | REF |

### pattern-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | REF |
| `cro/expert/detectors/tiabtc.py` | 1346 | __future__, cro, shared, typing | REF |
| `research/outputs/exp_va_cognitive_verification.md` | 1184 | — | REF |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | REF |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | REF |
| `tests/test_structure.py` | 1056 | cro, inspect, pytest, shared | REF |
| `docs/design/exp01e_tiabtc_bindings.md` | 1007 | — | REF |
| `tests/test_exp01d_crypto_punks.py` | 920 | ast, cro, hashlib, inspect, json | REF |
| `cro/expert/trees/crypto_punks.json` | 910 | — | REF |
| `docs/design/exp01d_crypto_punks_bindings.md` | 872 | — | REF |
| `docs/collab/CURRENT_STATE.md` | 748 | — | REF |
| `cto/m3_signals/signal_adapter/rules/chart_patterns.py` | 678 | __future__, build, shared | REF |

### ratchet-management

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `research/outputs/exp03b_v3_2_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_4_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_5_fills/tiabtc_struct.json` | 32856 | — | REF |
| `research/outputs/exp03b_v3_1_fills/tiabtc_struct.json` | 30666 | — | REF |
| `research/outputs/exp03b_v3_fills/tiabtc_struct.json` | 29182 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `tests/test_exp03a_kit.py` | 896 | cro, dataclasses, hashlib, json, pathlib | REF |
| `shared/backtest_kit.py` | 648 | __future__, collections, dataclasses, hashlib, json | REF |
| `research/scripts/exp03b_preq.py` | 578 | __future__, argparse, contextlib, cro, dataclasses | REF |
| `docs/collab/task_registry.md` | 471 | — | REF |
| `research/outputs/exp_gate1_material.md` | 402 | — | REF |
| `research/scripts/exp_regime_stratify.py` | 283 | __future__, collections, cro, datetime, json | REF |
| `research/harness.py` | 272 | __future__, cro, datetime, numpy, os | REF |
| `tests/test_pa_paper.py` | 240 | cro, json, pytest | REF |
| `tests/test_swing_paper.py` | 223 | cro, json, numpy, pytest, shared | REF |

### smc-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `frontend/package-lock.json` | 9926 | — | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `shared/structure.py` | 1427 | __future__, dataclasses, math | REF |
| `cto/m3_signals/signals.py` | 1332 | __future__, datetime, threading | REF |
| `cto/m5_backtest/m4_backtest.py` | 1154 | argparse, collections, concurrent, cto, datetime | REF |
| `cro/expert/detectors/giantcutie.py` | 1125 | __future__, bisect, cro, shared | REF |
| `cro/expert/detectors/crypto_punks.py` | 1084 | __future__, coo, cro, shared | REF |
| `tests/test_structure.py` | 1056 | cro, inspect, pytest, shared | REF |
| `tests/test_exp01c_giantcutie.py` | 1039 | ast, cro, inspect, json, pathlib | REF |
| `coo/run_pipeline.py` | 790 | __future__, argparse, asyncio, cfo, cto | REF |
| `cto/m5_backtest/train_m35.py` | 674 | argparse, cto, data, datetime, json | REF |
| `cro/expert/detectors/xiaom924.py` | 646 | __future__, cro, shared | REF |
| `tests/test_exp01b_xiaom924.py` | 633 | cro, json, pathlib, pytest, re | REF |

### war-room-dashboard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `docs/collab/archive/claude_to_deepseek_archive.md` | 13284 | @/components/providers/PnlProvider, @/components/ui/button, lightweight-charts | REF |
| `docs/collab/claude_to_deepseek.md` | 7068 | — | REF |
| `docs/collab/deepseek_to_claude.md` | 5290 | — | REF |
| `docs/collab/archive/deepseek_to_claude_archive.md` | 3743 | @/components/ui/button | REF |
| `frontend/app/pnl/page.tsx` | 735 | @/components/ui/badge, @/components/ui/card, @/contexts/PnlContext, @/lib/apiBase, @/lib/apiFetch | REF |
| `docs/collab/task_registry.md` | 471 | — | REF |
| `CLAUDE.md` | 449 | — | REF |
| `server/ws.py` | 408 | asyncio, ceo, coo, cro, datetime | REF |
| `docs/crypto_agent_ref/CLAUDE_original.md` | 346 | — | REF |
| `docs/design/dashboard_pages.md` | 328 | — | REF |
| `.claude/settings.local.json` | 280 | — | REF |
| `docs/collab/health_remediation_plan.md` | 253 | — | REF |
| `coo/api/operations.py` | 240 | datetime, fastapi, json, logging, server | REF |
| `server/main.py` | 224 | asyncio, ceo, cfo, ciso, cmo | REF |
| `docs/design/org_charter.md` | 204 | — | REF |
