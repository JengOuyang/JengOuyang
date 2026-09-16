# 策略持續優化循環（OPTIMIZATION_CYCLE.md）— 版本 1.0

> 這份文件回答：**「策略不會自己變好。誰、多久、用什麼證據、依什麼門檻去改它？」**
> 所有數值集中在 `shared/strategy_params.yaml: optimization`；本文件的變更走 `RISK_RULES.md` H 節並由 Blacksheep `!approve`。

## 0. 為什麼要有固定週期

沒有固定週期會出現兩種失敗，而且都很常見：

| 失敗 | 樣子 | 這裡怎麼防 |
|---|---|---|
| **過度反應** | 連虧三筆就改參數，把雜訊當訊號，策略被改成過去一週的樣子 | 只在**固定時點**改；期中除非觸發熔斷，否則不動參數 |
| **完全不動** | 市場 regime 換了半年，策略還在跑 2023 年的假設 | 季審**強制執行**，即使績效還可以也要跑；沒有「這季跳過」的選項 |

**核心原則：診斷可以隨時做，處方只在固定時點開。**

## 1. 三個層級的節奏

| 層級 | 頻率 | 主責 | 能改什麼 | 需要誰核准 |
|---|---|---|---|---|
| **L1 週檢視** | 每週 | AUDIT | **什麼都不能改**。只產出假設清單 | — |
| **L2 月審**（`OPT_MONTHLY`） | 每月 1 號 | AUDIT + RISK | **提名**停用候選；覆核 `v_setup_winrates`。自己不改任何檔案 | 停用需 Blacksheep `!approve`（WATCH 寫入） |
| **L3 季審**（`OPT_QUARTERLY`） | 每 3 個月（1/4/7/10 月 7 號） | LAB 主導，REDTEAM + RISK 審 | **參數本體**：止損 ATR 倍數、min_rr、型態門檻、時框、setup 定義 | REDTEAM 通過 → RISK 簽核 → **Blacksheep `!approve`** |

L1 → L2 → L3 是**證據的升級管道**：週檢視的觀察是 `UNVERIFIED`，月審通過樣本量檢定變 `VALIDATED`，季審通過回測與盲審才變 `PROMOTED`（寫進 `shared/`）。這與憲法第七條的知識三階段是同一套規則。

## 2. L2 月審（每月 1 號，約 30 分鐘人工時間）

**觸發**：`[CRON:audit-monthly]` → AUDIT 產出 `OPT_MONTHLY` 報告 → @RISK @CEO。

必答的六個問題（缺一項報告視為不完整，CEO 應退件）：

1. 本月各 setup 的 n、win_rate、expectancy、profit_factor，與**上月**及**回測基準**的差距。
2. `stop_reason` 分佈：結構性／噪音／執行性各佔多少？趨勢往哪邊走？
3. 哪些 setup 樣本已達 30 筆可以離開 `kelly_default_p = 0.40`？
4. 哪些 setup 連續兩個月 expectancy < 0（**停用候選**）？
5. **DRIFT 檢查**：實盤 expectancy / 回測 expectancy < 0.5 → 這是季審提前的觸發條件之一。
6. 型態學類 vs SMC 類的績效對比（避免其中一類長期拖累另一類卻被平均掩蓋）。

**月審能做的處置**（不需要回測，但**都不是 AUDIT 自己動手**）：

| 處置 | 誰提出 | 誰執行 | 需要核准嗎 |
|---|---|---|---|
| `v_setup_winrates` 重算（kelly_p 的來源） | — | `engine/metrics.py` 的排程（程式） | 否，這是統計事實不是參數變更；AUDIT 只覆核數字 |
| **停用**某個 setup（`enabled: false`） | AUDIT **提名**候選 → RISK 共同署名 | CEO 發 `HUMAN_DECISION_REQUIRED` → Blacksheep `!approve` → **WATCH** 寫入 `strategy_params.yaml` | **是**（憲法三：策略上線／下線是人類保留權限） |
| 重新啟用、改任何門檻數值 | — | — | **月審不得為之**，走季審 |

關掉一個 setup 不需要證明它更好，只需要證明它現在在虧——但「不需要更多證據」不等於「不需要核准」。
**AUDIT 沒有寫入權，它的所有處置都是提名。** 要放寬永遠比要收緊需要更多證據。

## 3. L3 季審（1/4/7/10 月 7 號，約 2 小時人工時間）

**這是真正的優化。** 由 `[CRON:lab-quarterly-refit]` 觸發，LAB 主導，流程固定七步：

| 步 | 誰 | 做什麼 | 產出 |
|---|---|---|---|
| 1 | AUDIT | 交出本季全部 TRADE_REVIEW 的結構化摘要 + 三個月的假設清單 | `OPT_EVIDENCE` |
| 2 | MACRO | 本季 **regime 判定**：趨勢／震盪／高波動，與前一季比較 | `REGIME_REPORT` |
| 3 | LAB | 對每個假設跑完整回測：8 年 + walk-forward（6 段）+ 參數擾動 ±20% + Monte Carlo 1000 次 | `BACKTEST_REPORT` |
| 4 | LAB | **重新擬合但不重新最佳化**：用最新資料重跑 walk-forward，檢查現行參數是否仍在**參數高原**上（見 §4） | `REFIT_REPORT` |
| 5 | REDTEAM | 盲審 + **自己重跑** `--verify`；特別審過度擬合徵狀 | `REVIEW_RESULT` |
| 6 | RISK | 風險簽核：MaxDD、連續虧損、Monte Carlo 5% 尾部、群組集中度 | `RISK_SIGNOFF` |
| 7 | CEO → Blacksheep | 彙整成一頁 `HUMAN_DECISION_REQUIRED`：**改什麼、為什麼、風險是什麼、不改會怎樣** | 你 `!approve` |

核准後：WATCH 寫入 `strategy_params.yaml` → 版本號 +1 → **模擬盤 4 週**（`demo_weeks_before_live`）→ 實盤。
**參數變更不會當天上線。** 這一條沒有例外。

## 4. 參數高原（Parameter Plateau）— 防過度擬合的主要工具

一個好參數不該是尖峰，而該是**高原**：把它上下移動 20%，績效不應該崩掉。

- 季審第 4 步對每個關鍵參數做 ±20% 擾動（`param_perturbation_pct`）。
- **通過**：擾動後 expectancy 仍 ≥ 現行的 70%。
- **不通過**：該參數目前的值是曲線擬合出來的，**即使它的回測數字最好也不採用**，改用高原中心值。

這是為什麼季審叫「重新擬合」而不是「重新最佳化」——我們找的是穩健區間，不是歷史最佳點。

## 5. 提前觸發（不必等到季審）

以下任一成立，CEO 立即發起**臨時季審**（流程完全相同，不簡化）：

| 觸發 | 門檻 |
|---|---|
| DRIFT | 滾動 30 筆的實盤 expectancy < 回測的 50% |
| 連續虧損 | 超過回測 Monte Carlo 95 百分位的最長連虧 |
| 回撤 | 帳戶回撤 ≥ 8%（12% 是停機，8% 是檢討） |
| Regime 反轉 | MACRO 判定 regime 改變且 CHART 的 htf_bias 在兩週內多次 MSS 翻轉 |
| 結構性止損異常 | 月審中「結構性」止損佔比連續兩月 > 50% |

## 6. 不做什麼（同樣重要）

- **不做期中參數微調**。想改就等下一個時點；急到不能等，代表那是熔斷事件不是優化事件。
- **不因單月績效好就放寬風控**。放寬永遠需要季審 + 回測 + 你核准。
- **不讓 CHART 參與參數決策**。它是提案者，不是評分者（憲法第八條、Goodhart 防護）。
- **不追求每季都有變更**。「本季維持現狀」是完全合法、而且常常是正確的結論——但**必須是跑完流程後的結論**，不是跳過流程。
