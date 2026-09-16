# 風控規則（RISK_RULES.md）— 版本 2.1（四層商品宇宙 · 分節切片版）

本文件是 RISK 的 Risk Gate（`engine/risk_gate.py`）的規格。所有數值集中在 `shared/strategy_params.yaml`；本文件與該檔的任何變更都必須走 H 節流程並由 Owner `!approve`。

**分節原則**：A 節是「提案者需要知道的要件」，G 節是「Gate 才需要知道的門檻」。CHART 只會拿到 A 節，看不到 G 節的數值——這是刻意的，避免它把分析優化成「剛好通過檢查」而不是「找到好交易」。

## A. 提案要件（CHART 必須滿足，否則不要提案）

| 編號 | 要件 | 說明 |
|---|---|---|
| A1 | **順勢** | `plan.direction` 必須等於當日 `htf_context.tradeable_direction`；為 NONE 時不提案 |
| A2 | **不與總經衝突** | `macro_brief.bias` 明確相反且高信心時不提案 |
| A3 | **止損必填且在結構外** | 多單 SL 低於進場參考的 1H swing low，空單反之；並留 ATR 緩衝 |
| A4 | **止損距離合理** | 不可貼太近（被正常波動打到）也不可過遠（風險報酬失衡）；以 ATR14(1H) 為尺 |
| A5 | **盈虧比達標** | 以 TP1 計的 RR 必須達到現行門檻（見 `strategy_params.yaml: risk.min_rr`） |
| A6 | **交易時段** | T3/T4 標的必須在 `session_open = true` 的 1H bar 才提案 |
| A7 | **資料品質** | 該標的近期無 SUSPECT 資料；有則降低 confidence 並註明 |
| A8 | **完整性** | 產出必須通過 `shared/schemas/trade_plan.schema.json` 驗證 |

被退件時你會收到「理由類別」（例如 `RR_INSUFFICIENT`、`COUNTER_TREND`、`SESSION_CLOSED`），不會收到門檻數值。請據此改善分析，而不是調整數字去通過檢查。

## G. Gate 檢查與門檻（僅 RISK / LAB / REDTEAM / FORGE）

逐條檢查，任一不過即 `REJECTED`，`reasons[]` 帶規則編號與實際數值。

| 編號 | 規則 | 門檻 |
|---|---|---|
| G1 | 順勢（對應 A1） | `tradeable_direction != NONE` 且方向一致 |
| G2 | 總經不衝突（對應 A2） | 相反且 `macro.confidence ≥ 0.6` → 拒 |
| G3 | 止損在結構外（對應 A3） | 以 `indicators.swing_lo/hi` 驗證 |
| G4 | 止損距離（對應 A4） | ∈ [0.5, 3.0] × ATR14(1H) |
| G5 | 盈虧比（對應 A5） | RR(TP1) ≥ 2.0 |
| G6 | 期望值 | `EV = p×R − (1−p) ≥ 0.15`；p = AUDIT 提供該 setup_type 近 100 筆勝率，樣本 < 30 筆時 p = 0.40 |
| G7 | 事件窗口 | 任一 HIGH 事件 `start − 2h` ～ `end + 30m` 內拒絕 |
| G8 | 交易時段與流動性（對應 A6） | T3 於 COMEX 休市、T4 於美股非交易時段拒絕；點差 > 3 bp 或 ±2% 深度低於 `universe.yaml` 門檻拒絕；T3/T4 基差 > 0.5% 拒絕 |
| G9 | 資料品質（對應 A7） | 進場時框最近 24 根 K 線無 SUSPECT |
| G10 | 加碼限制 | 同標的同方向最多加碼 1 次，合計風險不超過單筆上限 |
| G11 | 紅隊意見 | REDTEAM `DISAGREE` → `risk_amount × 0.5` |
| G12 | 相關性群組曝險 | 每群組名目 ≤ 3× equity、全帳戶 ≤ 5×、同時 ≤ 3 部位、同群組 ≤ 2 部位 |
| G13 | T2 山寨幣 | 單筆風險上限 1.0%（非 1.5%）；資金費率 > 0.1%/8h 禁同向開單；上市 < 3 年拒絕 |
| G14 | 事件日視同警告 | T4 財報日 ±1 交易日、指數再平衡日；T3 FOMC/CPI |
| G15 | 版本閘 | LIVE 模式下策略版本未經 Owner 核准 → 拒絕全部 |

## B. 倉位計算

```
p            = rolling_winrate(setup_type)            # AUDIT 提供，樣本 < 30 用 0.40
R            = plan.rr
kelly_f      = p - (1 - p) / R
cap          = 0.015                                  # T2 為 0.010
risk_pct     = min(cap, max(0, kelly_f) * 0.5)        # 二分之一凱利（strategy_params.risk.kelly_fraction）
risk_amount  = equity_total * risk_pct                # equity 取交易所 total equity（含未實現）
qty          = floor_to_step(risk_amount / abs(entry - stop_loss), contract_step)
notional     = qty * entry
leverage     = ceil(notional / (equity_total * 0.10)) # 保證金占用 ≈ 10% equity，上限 10x
```
- `qty < min_qty` → 拒絕（風險太小代表止損太遠或帳戶太小）。
- `notional` 使曝險超過 G12 上限 → 拒絕。

## C. 帳戶級規則（每次核准前 + 每 5 分鐘）

| 編號 | 規則 | 觸發後 |
|---|---|---|
| C1 | 單日已實現＋未實現虧損 ≥ 3% | 停開新單至次日 00:00 UTC |
| C2 | 單週虧損 ≥ 6% | 停至下週一並開檢討會 |
| C3 | 連續 4 筆止損 | 暫停 24h；AUDIT 出報告 |
| C4 | 權益自高點回撤 ≥ 12% | HALT：撤單、平倉、鎖定；Owner `!unlock` 才恢復 |
| C5 | 曝險上限 | 單一標的 ≤ 3× equity；每群組 ≤ 3×；全帳戶 ≤ 5× |
| C6 | 部位數 | 同時 ≤ 3；同群組 ≤ 2 |
| C7 | 交易所 API 連續 3 次失敗或對帳不一致 | 停開新單，WATCH 告警 |
| C8 | 上下文完整性驗證失敗 | 停開新單，@FORGE |

## D. 執行層規則（EXEC 程式必守）

| 編號 | 規則 |
|---|---|
| D1 | 進場成交後 10 秒內必須有倉位級止損單存在；否則市價平倉並告警 |
| D2 | 止損／止盈觸發價使用 mark_price |
| D3 | 止損只能向有利方向移動（棘輪），永不放寬 |
| D4 | 每份 plan 只允許一個 clientOid；重送前必須先查詢是否已存在 |
| D5 | 逐倉模式；槓桿依 B 節計算，上限 10x |
| D6 | 收到 `!flatten` 或 C4/C7 → 撤所有單、市價平所有倉、狀態設 HALT |
| D7 | DEMO 模式使用 `enable_demo_trading(True)`；LIVE 需 `mode: LIVE` 且版本已核准 |

## E. 棘輪（Ratchet）規則

| 階段 | 條件 | 動作 |
|---|---|---|
| R0 | 進場 | SL = plan.stop_loss；TP1/TP2/TP3 掛限價 |
| R1 | 未實現 ≥ +1.0R | SL → 進場價 ± 手續費（保本） |
| R2 | TP1 成交（+2R，平 40%） | SL → +0.5R |
| R3 | 之後每 5 分鐘 | SL = max(SL, min(1H 最後確認 swing low − 0.3×ATR, close − 3×ATR))（多單；空單鏡像） |
| R4 | TP2（+3R，平 30%） | 繼續 R3 追蹤剩餘 30% 直到 SL 觸發或 TP3（+5R） |
| RH | EVENT_WARNING 且 ≥ +1R 且 `ratchet.hedge_lock=true` | 開等量反向部位鎖利；事件後 30 分鐘由 CHART 評估解除方向 |

## H. 誰能改什麼

- A/G/B/C/D/E 的數值：Owner `!approve` 後由 WATCH 更新 `strategy_params.yaml` 並寫入 `config_versions`。
- 本文件的分節結構變更：FORGE 提案 → REDTEAM 審 → Owner 核准 → 重跑 `build_context.py`。
- MACRO 可新增事件到日曆，不可改窗口長度。
- CHART 可建議 `structure_stop`，EXEC 只在比現有 SL 更有利時採用。
