# 統一績效量尺（METRICS_SPEC.md）— metrics_version 2.0

所有績效數字（回測、模擬盤、實盤、Dashboard、報告）只能由 `engine/metrics.py` 計算；任何報告必須標註 `metrics_version`。

## 1. 基本單位：R
- `initial_risk = |entry_avg − initial_stop|`（以「初始止損」為準，棘輪後不變）
- `R = sign × (exit_avg − entry_avg) / initial_risk`，多單 sign=+1、空單 sign=−1
- 部分平倉：以各部分數量加權的平均出場價計算單一 R。
- 手續費與資金費率：計入 `R_net`；報表預設用 `R_net`。

## 2. 交易層指標（以已平倉交易為母體）
| 指標 | 定義 |
|---|---|
| n_trades | 已平倉交易數 |
| win_rate | R_net > 0.1 的比例 |
| breakeven_rate | R_net ∈ [−0.1, 0.1] 的比例 |
| loss_rate | R_net < −0.1 的比例 |
| expectancy | mean(R_net) |
| avg_win / avg_loss | 獲利單／虧損單平均 R_net |
| profit_factor | Σ 正 R_net ÷ |Σ 負 R_net| |
| payoff_ratio | avg_win ÷ |avg_loss| |
| MAE / MFE | 持倉期間最大不利／有利偏移（R 單位，用 1H 極值） |
| avg_hold_hours | 平均持倉小時 |
| max_consecutive_losses | 最長連續虧損 |

## 3. 權益層指標（以每小時權益曲線，含未實現）
| 指標 | 定義 |
|---|---|
| total_return | equity_end / equity_start − 1 |
| CAGR | (equity_end/equity_start)^(365/days) − 1 |
| daily_returns | 每日 00:00 UTC 權益的對數報酬 |
| Sharpe | mean(daily_returns) / std(daily_returns) × √365，rf = 0 |
| Sortino | 同上，分母用下行標準差 |
| MaxDD | max over t of (peak_t − equity_t) / peak_t，以每小時權益計 |
| Calmar | CAGR ÷ MaxDD |
| exposure | 有部位的時間比例 |
| ulcer_index | √mean(dd_t²) |

## 4. 回測報告必含區塊
1. 資料期間、來源、成本假設（手續費、資金費率、滑價、止損劣化）
2. 全期指標 + 每段 Walk-forward 的樣本外指標（6 段各自列出，再列合併）
3. 參數表與 ±20% 擾動結果（表格）
4. 逐年績效表（2018–2026）
5. Monte Carlo 1000 次重抽的 MaxDD 5%/50%/95% 分位
6. 與現行版本比較表（同一段樣本外期間）
7. 交易明細 CSV 路徑

## 5. 實盤／模擬盤日報必含
當日 R 合計、n、win_rate、expectancy、當前 MaxDD、最近 30 筆 expectancy vs 回測樣本外 expectancy（DRIFT 檢查）。

## 6. 版本
量尺任何修改 → metrics_version +0.1，舊報表不得與新報表直接比較，需重算。

## 7. Agent KPI 的量測歸屬（憲法第八條：我不替自己打分數）

**規則：沒有外部量測者的 KPI 不得寫進 MANUAL。** 自己算自己的分數不構成證據。

| Agent | KPI | 量測者 | 資料來源 |
|---|---|---|---|
| MACRO | MACRO_CONFLICT 止損占比、regime 判定的事後正確率 | AUDIT | `v_trade_journal` |
| FEED | 採集準時率、資料缺口數 | WATCH | `v_data_quality` |
| LEDGER | hash chain 驗證通過率、還原測試成功率 | WATCH | `v_backup_status`、`v_data_quality` |
| CHART | 各 setup_type 的 expectancy、RISK 退件率 | AUDIT | `v_setup_winrates`、`v_risk_decisions` |
| RISK | 否決後續被證實率、Gate 誤放行數 | AUDIT | `v_risk_decisions` + `v_trade_journal` |
| EXEC | 下單延遲、止損缺失次數、對帳不一致次數、冪等違規 | **WATCH**（非 EXEC 自報） | `v_agent_status`、`v_open_positions` |
| LAB | REDTEAM 發現的 look-ahead 次數、樣本外/樣本內衰減 | REDTEAM | `BACKTEST_REPORT` 重跑結果 |
| REDTEAM | DISAGREE 後續被證實率 | AUDIT | `v_trade_journal` |
| AUDIT | 解剖延遲、stop_reason 分類率 | **WATCH**（AUDIT 是量尺，量尺也要被量） | `v_agent_status` |
| WATCH | 告警準確率＝告警後 24h 內確實發生問題的比例 | **AUDIT**（在月報中回報） | `v_agent_status` + 事件紀錄 |
| FORGE | 回歸 bug 率、修復後 24h 內同類錯誤數 | WATCH | `v_fix_log`、`logs/` |
| CEO | Blacksheep 每日投入時間（代理指標：`#human-inbox` 的訊息則數 + `HUMAN_DECISION_REQUIRED` 則數）、逾期任務數、24h 審核率 | **WATCH**（系統週報，不經 CEO） | `v_task_board` |
| CMO | 各支柱 KPI 達成率 | GROWTH | `GROWTH_REPORT` |
| CREATIVE | save_rate、engagement_rate、Owner 一次核准率 | GROWTH + Owner | `v_content_pipeline` |
| GROWTH | 實驗結論的可重現率 | CMO | 月度對照 |

**AUDIT 與 WATCH 互相量測**：AUDIT 的延遲由 WATCH 的心跳量，WATCH 的告警準確率由 AUDIT 在月報中量。
這是刻意的閉環——系統裡最後兩個「量別人的人」不能都沒有人量。
