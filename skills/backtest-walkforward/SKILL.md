---
name: backtest-walkforward
description: LAB 回測、Walk-forward、參數擾動、Monte Carlo、報表
---

# backtest-walkforward

## 何時使用
LAB 回測、Walk-forward、參數擾動、Monte Carlo、報表。

## 輸入 / 輸出契約
- **輸入**：策略版本 + 參數 + 資料期間
- **輸出**：`BACKTEST_REPORT`（全期 + 6 段 OOS + 擾動 + Monte Carlo + acceptance 判定）
- **失敗時**：資料缺口或成本假設不明 → 標註並在報告中單獨列出受影響區間

## 步驟
1. 資料 2018-09-01 起；T1 Binance 補；T3/T4 現貨拼接並標基差；T4 只用美股時段 bar。
2. 成本：taker 0.06%/maker 0.02%、funding 歷史、滑價 2bp、止損下一根最差價。
3. 6 段 WF（16/8 月）、±20% 擾動、MC 1000。
4. acceptance 對照 strategy_params.backtest.acceptance；T3/T4 另列 Bitget 真實期間。
5. 固定 seed 與資料版本供 REDTEAM 重跑。

## 完成檢查
- [ ] OOS 指標齊全
- [ ] 無 look-ahead

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `backtest/engine.py`
- `backtest/report.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
