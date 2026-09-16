---
name: pattern-analysis
description: CHART 做古典型態學辨識（頭肩、雙頂底、三角、旗形、楔形、矩形）與 MSS 判定時使用
---

# pattern-analysis

## 何時使用
CHART 在日線／4H 做**古典型態學**辨識，或需要判定 **MSS（市場結構轉變）** 是否成立時使用。
與 `smc-analysis` **並用而非二選一**：型態學給「這是什麼形狀、目標在哪」，SMC 給「誰在這裡被套、流動性在哪」。兩者指向同一個價位時才是高信心匯合。

## 輸入 / 輸出契約
- **輸入**：`v_market`（1D / 4H OHLCV）、`v_indicators`（ATR14、20 根均量）、`scripts/patterns.py` 的辨識結果
- **輸出**：`pattern_type`、型態邊界價位、頸線／突破價、量價確認結果、measured-move 目標、`pattern_confidence`
- **失敗時**：辨識不到符合門檻的型態 → 不要「看起來像」就寫進去，直接回報無型態（`pattern_type: NONE`）

## 步驟

1. **跑程式，不憑視覺**：`python ../../scripts/patterns.py --symbol <S> --tf 1D` 取候選型態。
   參數在 `strategy_params.analysis.patterns`：成形 15–120 根、突破需超出頸線 0.3 ATR。
2. **量價確認**：突破 K 棒成交量 ≥ 前 20 根均量 × 1.5（`volume_confirm_ratio`）。
   **不過就是假突破，不提案。** 這是型態學最常見的虧損來源。
3. **MSS 判定**（`strategy_params.analysis.mss`）：
   - CHoCH 出現 → 只是**警訊**，不翻 `htf_bias`。
   - 收盤價站穩被破壞結構點外 ≥ 0.25 ATR → 候選 MSS。
   - 12 根內回測不破 → **MSS 成立**，此時才翻 `htf_bias`，並可用 `MSS_RETEST` setup。
   - 12 根內破回去 → 型態失效，記錄為 `MSS_FAILED`（AUDIT 要統計這個）。
4. **目標價**：measured move（型態高度投影）與 Fib 1.272 / 下一個 POC 取**較近者**——型態學的目標常過度樂觀。
5. **與 SMC 交叉**：型態的頸線／邊界是否同時是 OB、FVG 或流動性池？是 → `pattern_confidence` +0.1；只有型態、沒有任何 SMC 依據 → 上限 0.6。
6. 寫入 `TRADE_PLAN` 時 `setup_type` 用型態類代碼（`HS_NECKLINE_BREAK` 等），讓 AUDIT 能分開統計型態學與 SMC 的勝率。

## 完成檢查
- [ ] 型態來自程式辨識，不是「我覺得像頭肩頂」
- [ ] 量價確認通過（或明確標註未通過並因此不提案）
- [ ] 目標價取 measured move 與 Fib/POC 的較近者
- [ ] MSS 只在「收盤站穩 + 回測不破」都成立時才宣告
- [ ] `setup_type` 用型態代碼，不混進 SMC 代碼

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/patterns.py`（辨識器）
- `backtest/`（LAB 需分別回測型態學類與 SMC 類的 expectancy）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 `scripts/patterns.py`，一併複製並調整路徑。
