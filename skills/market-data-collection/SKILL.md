---
name: market-data-collection
description: FEED 採集四層宇宙行情與指標（程式技能）
---

# market-data-collection

## 何時使用
FEED 採集四層宇宙行情與指標（程式技能）。

## 輸入 / 輸出契約
- **輸入**：universe.yaml 的啟用標的清單 + 上次採集時間
- **輸出**：寫入 ohlcv/funding/oi/orderbook_snap/indicators 的列數與 `suspect` 標記
- **失敗時**：缺根或交叉驗證偏差 > 0.5% → 標 SUSPECT 並發 DATA_ALERT，不要靜默補值

## 步驟
1. ccxt 公開端點：fetch_ohlcv（1h/4h/1d/1w/1M 增量）、fetch_funding_rate、fetch_open_interest、fetch_order_book（±2% 深度、點差）。
2. Binance 交叉驗證；CoinGecko 市值（T2）。
3. 指標：EMA20/50/200、ATR14、RSI14、VWAP、Volume Profile（POC/VAH/VAL 30/90 日）、fractal swing、結構標記、session_open。
4. 寫入經 LEDGER ingest（token FEED）。
5. 異常 → DATA_ALERT。

## 完成檢查
- [ ] 最後一根 K 線已收線
- [ ] 每 symbol/tf 有 UNIQUE 約束

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/collect_hourly.py`
- `scripts/compute_indicators.py`
- `scripts/refresh_universe.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
