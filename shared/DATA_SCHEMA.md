# 資料倉 Schema（DATA_SCHEMA.md）— schema_version 1.0

儲存：SQLite（WAL 模式）`data/tradedesk.db`；每日 Parquet 冷備 `data/parquet/<table>/<date>.parquet`。
通則：所有表皆 append-only；每筆含 `row_id`（自增）、`ingest_ts`、`writer`（哪個程式 token）、`prev_hash`、`row_hash`。
`row_hash = sha256(prev_hash + canonical_json(業務欄位))`，`canonical_json` = 鍵排序、無空白、UTF-8。

## 市場資料
```sql
CREATE TABLE ohlcv (row_id INTEGER PRIMARY KEY, symbol TEXT, tf TEXT, ts INTEGER,
  o REAL, h REAL, l REAL, c REAL, v REAL, quote_v REAL, source TEXT, suspect INTEGER DEFAULT 0,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT,
  UNIQUE(symbol, tf, ts, source));
CREATE TABLE funding (row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER, rate REAL, predicted_rate REAL, source TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE oi (row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER, oi REAL, oi_usd REAL, long_short_ratio REAL, liq_long_24h REAL, liq_short_24h REAL, source TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE orderbook_snap (row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER, bid_depth_2pct REAL, ask_depth_2pct REAL, spread_bp REAL, source TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE indicators (row_id INTEGER PRIMARY KEY, symbol TEXT, tf TEXT, ts INTEGER,
  ema20 REAL, ema50 REAL, ema200 REAL, atr14 REAL, rsi14 REAL, vwap_d REAL, vwap_w REAL,
  poc_30d REAL, vah_30d REAL, val_30d REAL, poc_90d REAL, vah_90d REAL, val_90d REAL,
  swing_hi REAL, swing_lo REAL, structure TEXT,  -- HH/HL/LH/LL/RANGE
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT, UNIQUE(symbol, tf, ts));
```

## 分析與決策
```sql
CREATE TABLE macro_brief (row_id INTEGER PRIMARY KEY, date TEXT, regime TEXT, bias TEXT, confidence REAL, events_json TEXT, summary TEXT, sources_json TEXT, model TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE htf_context (row_id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, context_json TEXT, htf_bias TEXT, tradeable_direction TEXT, skeptic_verdict TEXT, model TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE trade_plan (row_id INTEGER PRIMARY KEY, plan_id TEXT UNIQUE, symbol TEXT, direction TEXT, setup_type TEXT, plan_json TEXT, confidence REAL, rr REAL, skeptic_verdict TEXT, model TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE risk_decision (row_id INTEGER PRIMARY KEY, plan_id TEXT, approved INTEGER, risk_pct REAL, risk_amount REAL, qty REAL, leverage REAL, kelly_p REAL, ev REAL, reasons_json TEXT, params_version TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
```

## 執行
```sql
CREATE TABLE orders (row_id INTEGER PRIMARY KEY, order_id TEXT, client_oid TEXT, plan_id TEXT, symbol TEXT, side TEXT, trade_side TEXT, type TEXT, price REAL, qty REAL, status TEXT, purpose TEXT, -- ENTRY/SL/TP1/TP2/TP3/HEDGE/FLATTEN
  raw_json TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE fills (row_id INTEGER PRIMARY KEY, fill_id TEXT UNIQUE, order_id TEXT, plan_id TEXT, symbol TEXT, side TEXT, price REAL, qty REAL, fee REAL, ts INTEGER, raw_json TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE positions (row_id INTEGER PRIMARY KEY, snapshot_ts INTEGER, symbol TEXT, side TEXT, qty REAL, entry_avg REAL, mark REAL, unrealized REAL, sl_price REAL, tp_prices_json TEXT, ratchet_stage TEXT, plan_id TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE equity_curve (row_id INTEGER PRIMARY KEY, ts INTEGER, equity REAL, balance REAL, unrealized REAL, mode TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
```

## 檢討與治理
```sql
CREATE TABLE trade_journal (row_id INTEGER PRIMARY KEY, trade_id TEXT UNIQUE, plan_id TEXT, symbol TEXT, direction TEXT, setup_type TEXT,
  entry_plan REAL, entry_actual REAL, sl_initial REAL, exit_avg REAL, r_gross REAL, r_net REAL, mae_r REAL, mfe_r REAL, hold_hours REAL,
  exit_reason TEXT, stop_reason TEXT, review_json TEXT, lessons TEXT, followup_task_id TEXT, model TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE agent_heartbeat (row_id INTEGER PRIMARY KEY, agent_id TEXT, ts INTEGER, task TEXT, status TEXT, model TEXT, tokens_in INTEGER, tokens_out INTEGER, duration_ms INTEGER, error TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE tasks (row_id INTEGER PRIMARY KEY, task_id TEXT, event TEXT, assignee TEXT, status TEXT, payload_json TEXT, score INTEGER, ts INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE config_versions (row_id INTEGER PRIMARY KEY, version TEXT UNIQUE, yaml_text TEXT, yaml_hash TEXT, change_id TEXT, approver TEXT, effective_ts INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE audit_anchor (row_id INTEGER PRIMARY KEY, date TEXT, table_name TEXT, row_count INTEGER, merkle_root TEXT, discord_msg_id TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE corrections (row_id INTEGER PRIMARY KEY, table_name TEXT, correction_of INTEGER, reason TEXT, new_values_json TEXT, approver TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
```

## 唯讀視圖（給 LLM Agent 與 Dashboard）
- `v_latest_ohlcv`、`v_latest_indicators`、`v_open_positions`、`v_today_pnl`、`v_setup_winrates`（每 setup_type 近 100 筆勝率）、`v_agent_status`。
- LLM Agent 只透過 `scripts/query_readonly.py`（`PRAGMA query_only=1`）查詢。

## 寫入 API（LEDGER ingest 服務）
`POST http://127.0.0.1:8787/ingest/<table>`，Header `X-Writer-Token`。每個寫入程式一個 token（INGEST_TOKEN_FEED、INGEST_TOKEN_EXEC、INGEST_TOKEN_AUDIT、INGEST_TOKEN_MACRO、INGEST_TOKEN_MARKETING（見 router/.env.example））。回傳 `row_id, row_hash`。

## v2 新增表
```sql
CREATE TABLE universe (row_id INTEGER PRIMARY KEY, tier TEXT, symbol TEXT, grp TEXT, action TEXT, -- ADD/REMOVE
  effective TEXT, source TEXT, rank INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE content (row_id INTEGER PRIMARY KEY, content_id TEXT UNIQUE, pillar TEXT, format TEXT, caption TEXT, image_paths_json TEXT,
  status TEXT, -- DRAFT/REVIEW/APPROVED/PUBLISHED/REJECTED
  approver TEXT, ig_media_id TEXT, permalink TEXT, published_ts INTEGER, metrics_24h_json TEXT, metrics_7d_json TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE ig_insights (row_id INTEGER PRIMARY KEY, date TEXT, followers INTEGER, reach INTEGER, impressions INTEGER, profile_visits INTEGER,
  website_clicks INTEGER, audience_json TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE bug_reports (row_id INTEGER PRIMARY KEY, bug_id TEXT UNIQUE, reporter TEXT, agent_id TEXT, severity TEXT, symptom TEXT,
  repro_json TEXT, status TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE fix_log (row_id INTEGER PRIMARY KEY, bug_id TEXT, commit_hash TEXT, files_json TEXT, tests_json TEXT, reviewer TEXT,
  approved_by TEXT, deployed_ts INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE llm_usage (row_id INTEGER PRIMARY KEY, ts INTEGER, agent_id TEXT, model TEXT, input_tokens INTEGER, output_tokens INTEGER,
  cost_usd_est REAL, duration_ms INTEGER, session_id TEXT, thread_id TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
```
