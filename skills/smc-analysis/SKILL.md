---
name: smc-analysis
description: CHART 做 SMC/價格行為分析（OB、FVG、流動性、BOS/CHoCH、缺口、POC、Fib）時使用
---

# smc-analysis

## 何時使用
CHART 做 SMC/價格行為分析（OB、FVG、流動性、BOS/CHoCH、缺口、POC、Fib）時使用。

## 輸入 / 輸出契約
- **輸入**：`v_market`、`v_indicators`、`v_levels` 的該標的資料
- **輸出**：匯合區清單與每個價位的依據（結構／ATR／Fib／POC）
- **失敗時**：資料 SUSPECT 或無匯合區 → `NO_SETUP`，不要降低標準硬找

## 步驟
1. 用 scripts/levels.py 取數值化候選：swing、結構、OB（含 mitigated）、FVG、等高等低流動性、未回補缺口（含 CME 週末缺口）、POC/VAH/VAL、Fib 0.5/0.618/0.786、1.272/1.618。
2. 定義：OB = 反向推動前最後一根反向 K；FVG = 三根 K 的不平衡（≥ 0.5 ATR）；BOS = 順向突破結構高低；CHoCH = 首次反向突破。
3. 匯合區 = ≥ 2 個候選重疊。
4. 止損 = 結構外 + 0.3 ATR；TP1 = 下一個對向流動性／POC／Fib 1.272。

## 完成檢查
- [ ] 每個價位有依據
- [ ] RR ≥ 2

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/levels.py`
- `scripts/prefilter_1h.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
