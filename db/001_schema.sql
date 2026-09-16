-- 001_schema.sql — 資料倉結構（append-only + hash chain）
-- 規格說明見 shared/DATA_SCHEMA.md。執行：sqlite3 data/tradedesk.db < db/001_schema.sql
PRAGMA journal_mode=WAL;

-- 通用欄位：row_id, ingest_ts, writer, prev_hash, row_hash
-- row_hash = sha256(prev_hash || canonical_json(業務欄位))

CREATE TABLE IF NOT EXISTS ohlcv(row_id INTEGER PRIMARY KEY, symbol TEXT, tf TEXT, ts INTEGER,
  o REAL,h REAL,l REAL,c REAL,v REAL,quote_v REAL, source TEXT, suspect INTEGER DEFAULT 0,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT, UNIQUE(symbol,tf,ts,source));
CREATE TABLE IF NOT EXISTS funding(row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER, rate REAL, predicted_rate REAL,
  source TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT, UNIQUE(symbol,ts));
CREATE TABLE IF NOT EXISTS oi(row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER, oi REAL, oi_usd REAL,
  long_short_ratio REAL, liq_long_24h REAL, liq_short_24h REAL, source TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT, UNIQUE(symbol,ts));
CREATE TABLE IF NOT EXISTS orderbook_snap(row_id INTEGER PRIMARY KEY, symbol TEXT, ts INTEGER,
  bid_depth_2pct REAL, ask_depth_2pct REAL, spread_bp REAL, source TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS indicators(row_id INTEGER PRIMARY KEY, symbol TEXT, tf TEXT, ts INTEGER,
  ema20 REAL,ema50 REAL,ema200 REAL,atr14 REAL,rsi14 REAL,vwap_d REAL,vwap_w REAL,
  poc_30d REAL,vah_30d REAL,val_30d REAL,poc_90d REAL,vah_90d REAL,val_90d REAL,
  swing_hi REAL, swing_lo REAL, structure TEXT, session_open INTEGER,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT, UNIQUE(symbol,tf,ts));
CREATE TABLE IF NOT EXISTS levels(row_id INTEGER PRIMARY KEY, symbol TEXT, tf TEXT, ts INTEGER,
  kind TEXT, low REAL, high REAL, mitigated INTEGER DEFAULT 0,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

CREATE TABLE IF NOT EXISTS macro_brief(row_id INTEGER PRIMARY KEY, date TEXT, regime TEXT, bias TEXT, confidence REAL,
  events_json TEXT, summary TEXT, sources_json TEXT, model TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS calendar_events(row_id INTEGER PRIMARY KEY, event TEXT, ts_utc INTEGER, impact TEXT,
  affects_json TEXT, source TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS htf_context(row_id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, context_json TEXT,
  htf_bias TEXT, tradeable_direction TEXT, redteam_verdict TEXT, model TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS trade_plan(row_id INTEGER PRIMARY KEY, plan_id TEXT UNIQUE, symbol TEXT, direction TEXT,
  setup_type TEXT, plan_json TEXT, confidence REAL, rr REAL, redteam_verdict TEXT, model TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS risk_decision(row_id INTEGER PRIMARY KEY, plan_id TEXT, approved INTEGER,
  risk_pct REAL, risk_amount REAL, qty REAL, leverage REAL, kelly_p REAL, ev REAL,
  reasons_json TEXT, params_version TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

CREATE TABLE IF NOT EXISTS orders(row_id INTEGER PRIMARY KEY, order_id TEXT, client_oid TEXT, plan_id TEXT,
  symbol TEXT, side TEXT, trade_side TEXT, type TEXT, price REAL, qty REAL, status TEXT, purpose TEXT,
  raw_json TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS fills(row_id INTEGER PRIMARY KEY, fill_id TEXT UNIQUE, order_id TEXT, plan_id TEXT,
  symbol TEXT, side TEXT, price REAL, qty REAL, fee REAL, ts INTEGER, raw_json TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS positions(row_id INTEGER PRIMARY KEY, snapshot_ts INTEGER, symbol TEXT, side TEXT,
  qty REAL, entry_avg REAL, mark REAL, unrealized REAL, sl_price REAL, tp_prices_json TEXT,
  ratchet_stage TEXT, plan_id TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS equity_curve(row_id INTEGER PRIMARY KEY, ts INTEGER, equity REAL, balance REAL,
  unrealized REAL, mode TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

CREATE TABLE IF NOT EXISTS trade_journal(row_id INTEGER PRIMARY KEY, trade_id TEXT UNIQUE, plan_id TEXT, symbol TEXT,
  direction TEXT, setup_type TEXT, entry_plan REAL, entry_actual REAL, sl_initial REAL, exit_avg REAL,
  r_gross REAL, r_net REAL, mae_r REAL, mfe_r REAL, hold_hours REAL, exit_reason TEXT, stop_reason TEXT,
  review_json TEXT, lessons TEXT, followup_task_id TEXT, model TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS perf_reports(row_id INTEGER PRIMARY KEY, period TEXT, n_trades INTEGER, win_rate REAL,
  expectancy REAL, max_dd REAL, sharpe REAL, signed_by TEXT, published INTEGER DEFAULT 0, metrics_version TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS backtest_reports(row_id INTEGER PRIMARY KEY, change_id TEXT, strategy_version TEXT,
  metrics_json TEXT, acceptance_pass INTEGER, artifacts_json TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

CREATE TABLE IF NOT EXISTS universe(row_id INTEGER PRIMARY KEY, tier TEXT, symbol TEXT, grp TEXT, action TEXT,
  effective TEXT, source TEXT, rank INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS content(row_id INTEGER PRIMARY KEY, content_id TEXT UNIQUE, pillar TEXT, format TEXT,
  caption TEXT, image_paths_json TEXT, status TEXT, approver TEXT, ig_media_id TEXT, permalink TEXT,
  scheduled_for TEXT, published_ts INTEGER, metrics_24h_json TEXT, metrics_7d_json TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS ig_insights(row_id INTEGER PRIMARY KEY, date TEXT, followers INTEGER, reach INTEGER,
  impressions INTEGER, profile_visits INTEGER, website_clicks INTEGER, audience_json TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

CREATE TABLE IF NOT EXISTS agent_heartbeat(row_id INTEGER PRIMARY KEY, agent_id TEXT, ts INTEGER, task TEXT,
  status TEXT, model TEXT, error TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS llm_usage(row_id INTEGER PRIMARY KEY, ts INTEGER, agent_id TEXT, model TEXT,
  input_tokens INTEGER, output_tokens INTEGER, cost_usd_est REAL, duration_ms INTEGER, session_id TEXT, thread_id TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS tasks(row_id INTEGER PRIMARY KEY, task_id TEXT, event TEXT, assignee TEXT, status TEXT,
  payload_json TEXT, score INTEGER, ts INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS bug_reports(row_id INTEGER PRIMARY KEY, bug_id TEXT UNIQUE, reporter TEXT, agent_id TEXT,
  skill_name TEXT,                       -- 失敗歸因到 skill 層級，而不只是 agent
  severity TEXT, symptom TEXT, repro_json TEXT, status TEXT,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);

-- 記憶治理：每一條「學到的東西」都從 UNVERIFIED 開始，驗證後才能升級
CREATE TABLE IF NOT EXISTS knowledge(row_id INTEGER PRIMARY KEY, knowledge_id TEXT UNIQUE,
  source_agent TEXT, domain TEXT,        -- setup / macro / execution / marketing / system
  claim TEXT,                            -- 一句話的主張
  evidence_json TEXT,                    -- 支持證據（trade_id、backtest change_id、樣本數）
  status TEXT DEFAULT 'UNVERIFIED',      -- UNVERIFIED → VALIDATED → PROMOTED（或 REJECTED）
  sample_n INTEGER, validated_by TEXT, validated_ts INTEGER,
  promoted_to TEXT,                      -- 若 PROMOTED，寫進了 shared/ 的哪一節
  approver TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS fix_log(row_id INTEGER PRIMARY KEY, bug_id TEXT, commit_hash TEXT, files_json TEXT,
  tests_json TEXT, reviewer TEXT, approved_by TEXT, deployed_ts INTEGER,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS config_versions(row_id INTEGER PRIMARY KEY, version TEXT UNIQUE, yaml_text TEXT,
  yaml_hash TEXT, change_id TEXT, approver TEXT, effective_ts INTEGER,
  ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS audit_anchor(row_id INTEGER PRIMARY KEY, date TEXT, table_name TEXT, row_count INTEGER,
  merkle_root TEXT, discord_msg_id TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS backups(row_id INTEGER PRIMARY KEY, date TEXT, backup_ok INTEGER, restore_test_ok INTEGER,
  path TEXT, bytes INTEGER, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS corrections(row_id INTEGER PRIMARY KEY, table_name TEXT, correction_of INTEGER,
  reason TEXT, new_values_json TEXT, approver TEXT, ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT);
CREATE TABLE IF NOT EXISTS system_state(key TEXT PRIMARY KEY, value TEXT, updated_ts INTEGER);
INSERT OR IGNORE INTO system_state VALUES('mode','DEMO',strftime('%s','now')),
 ('trading','RUNNING',strftime('%s','now')),('params_ver','2.1.0',strftime('%s','now'));

CREATE INDEX IF NOT EXISTS ix_ohlcv ON ohlcv(symbol,tf,ts);
CREATE INDEX IF NOT EXISTS ix_ind   ON indicators(symbol,tf,ts);
CREATE INDEX IF NOT EXISTS ix_hb    ON agent_heartbeat(agent_id,ts);
CREATE INDEX IF NOT EXISTS ix_usage ON llm_usage(ts,agent_id);
