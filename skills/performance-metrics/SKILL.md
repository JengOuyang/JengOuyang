---
name: performance-metrics
description: 計算或引用任何績效數字（回測、模擬、實盤、行銷績效貼文）時使用
---

# performance-metrics

## 何時使用
計算或引用任何績效數字（回測、模擬、實盤、行銷績效貼文）時使用。

## 輸入 / 輸出契約
- **輸入**：`trade_journal` / `equity_curve` 的資料範圍
- **輸出**：METRICS_SPEC 定義的指標字典 + `metrics_version`
- **失敗時**：算不出來就說資料不足，不要用近似值代替

## 步驟
1. 只用 engine/metrics.py（METRICS_SPEC 2.0）；不要手算 Sharpe/MaxDD。
2. 報表附 metrics_version、期間、是否含模擬盤。
3. R 以初始止損為分母；R_net 含費用。
4. 比較不同版本時必須同一段樣本外期間。

## 完成檢查
- [ ] metrics_version 標註
- [ ] 同一函式產出

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `engine/metrics.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
