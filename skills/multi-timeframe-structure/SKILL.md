---
name: multi-timeframe-structure
description: 判定 M/W/D/4H/1H 結構與 htf_bias、tradeable_direction 時使用
---

# multi-timeframe-structure

## 何時使用
判定 M/W/D/4H/1H 結構與 htf_bias、tradeable_direction 時使用。

## 輸入 / 輸出契約
- **輸入**：M/W/D/4H/1H 的 ohlcv 與 structure 欄位
- **輸出**：`{per_tf_structure, htf_bias, tradeable_direction}`
- **失敗時**：時框衝突時以較高時框為準並標註 RANGE 風險，不要自行折衷

## 步驟
1. 每時框：HH/HL → BULL；LH/LL → BEAR；否則 RANGE；記錄最近 BOS/CHoCH。
2. htf_bias 由 M/W/D 多數決，D 與 W 衝突時以 W 為準並標 RANGE 風險。
3. tradeable_direction：BULL → LONG_ONLY；BEAR → SHORT_ONLY；RANGE → 只在區間邊緣順 4H 方向；與 MACRO 衝突（confidence ≥ 0.6）→ NONE。
4. T3/T4 額外檢查 session。

## 完成檢查
- [ ] 每時框有結構標籤
- [ ] 衝突有說明

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- （純知識型技能，無程式）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
