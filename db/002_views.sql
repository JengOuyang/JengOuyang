-- 002_views.sql — 權限視圖層
-- 這是「認知隔離」的物理實作：LLM Agent 只能查視圖，欄位裁切在這裡完成，
-- 而不是靠 prompt 說「你不要看」。授權對應表見 shared/view_grants.yaml。
-- 執行：sqlite3 data/tradedesk.db < db/002_views.sql

-- ── 全體共用 ───────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_system_status AS
SELECT (SELECT value FROM system_state WHERE key='mode')        AS mode,
       (SELECT value FROM system_state WHERE key='trading')     AS trading_state,
       (SELECT value FROM system_state WHERE key='params_ver')  AS params_version,
       (SELECT MAX(ts) FROM equity_curve)                       AS last_equity_ts;

CREATE VIEW IF NOT EXISTS v_universe_active AS
SELECT tier, symbol, grp, effective FROM universe
WHERE action='ADD' AND symbol NOT IN (SELECT symbol FROM universe WHERE action='REMOVE');

CREATE VIEW IF NOT EXISTS v_calendar_upcoming AS
SELECT event, ts_utc, impact, affects_json FROM calendar_events
WHERE ts_utc >= strftime('%s','now') ORDER BY ts_utc LIMIT 50;

-- ── 行情與指標 ─────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_market AS
SELECT o.symbol, o.tf, o.ts, o.o, o.h, o.l, o.c, o.v, o.suspect,
       i.ema20, i.ema50, i.ema200, i.atr14, i.rsi14, i.structure, i.session_open
FROM ohlcv o LEFT JOIN indicators i ON i.symbol=o.symbol AND i.tf=o.tf AND i.ts=o.ts;

CREATE VIEW IF NOT EXISTS v_market_daily AS
SELECT * FROM v_market WHERE tf IN ('1d','1w','1M');

CREATE VIEW IF NOT EXISTS v_indicators AS
SELECT symbol, tf, ts, ema20, ema50, ema200, atr14, rsi14, vwap_d, vwap_w,
       poc_30d, vah_30d, val_30d, poc_90d, vah_90d, val_90d, swing_hi, swing_lo, structure, session_open
FROM indicators;

CREATE VIEW IF NOT EXISTS v_levels AS
SELECT symbol, tf, ts, kind, low, high, mitigated FROM levels;

CREATE VIEW IF NOT EXISTS v_funding_oi AS
SELECT f.symbol, f.ts, f.rate, f.predicted_rate, o.oi, o.oi_usd, o.long_short_ratio,
       o.liq_long_24h, o.liq_short_24h
FROM funding f LEFT JOIN oi o ON o.symbol=f.symbol AND o.ts=f.ts;

CREATE VIEW IF NOT EXISTS v_data_quality AS
SELECT symbol, tf, COUNT(*) AS rows, SUM(suspect) AS suspect_rows, MAX(ts) AS last_ts
FROM ohlcv GROUP BY symbol, tf;

-- ── 總經 ───────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_macro_current AS
SELECT date, regime, bias, confidence, summary FROM macro_brief ORDER BY date DESC LIMIT 1;
CREATE VIEW IF NOT EXISTS v_macro_history AS
SELECT date, regime, bias, confidence, summary FROM macro_brief ORDER BY date DESC LIMIT 180;

-- ── CHART：看得到退件「類別」，看不到門檻數值（防 Goodhart）────
CREATE VIEW IF NOT EXISTS v_reject_categories AS
SELECT p.symbol, p.setup_type, date(r.ingest_ts,'unixepoch') AS d,
       json_extract(r.reasons_json,'$[0].code') AS reason_code,   -- 只有代碼，無數值
       COUNT(*) AS n
FROM risk_decision r JOIN trade_plan p ON p.plan_id=r.plan_id
WHERE r.approved=0 GROUP BY p.symbol, p.setup_type, d, reason_code;

CREATE VIEW IF NOT EXISTS v_setup_winrates AS
SELECT setup_type, COUNT(*) AS n,
       AVG(CASE WHEN r_net>0.1 THEN 1.0 ELSE 0.0 END) AS win_rate,
       AVG(r_net) AS expectancy
FROM (SELECT setup_type, r_net FROM trade_journal ORDER BY row_id DESC LIMIT 100)
GROUP BY setup_type;

CREATE VIEW IF NOT EXISTS v_my_open_positions AS   -- 給 CHART 更新 structure_stop 用：無倉位大小
SELECT symbol, side, entry_avg, sl_price, ratchet_stage, plan_id FROM positions
WHERE snapshot_ts=(SELECT MAX(snapshot_ts) FROM positions);

-- ── REDTEAM 盲審：剔除 CHART 的推理與信心分數 ────────────────
CREATE VIEW IF NOT EXISTS v_blind_plan AS
SELECT plan_id, symbol, direction, setup_type,
       json_remove(plan_json,'$.reasoning','$.confidence') AS plan_json, ingest_ts
FROM trade_plan;

CREATE VIEW IF NOT EXISTS v_blind_htf AS
SELECT symbol, date, json_remove(context_json,'$.reasoning') AS context_json,
       htf_bias, tradeable_direction
FROM htf_context;

-- ── 風控與執行 ─────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_risk_decisions AS
SELECT plan_id, approved, risk_pct, risk_amount, qty, leverage, kelly_p, ev, reasons_json, params_version, ingest_ts
FROM risk_decision;

CREATE VIEW IF NOT EXISTS v_approved_orders AS
SELECT plan_id, qty, leverage, ingest_ts FROM risk_decision WHERE approved=1;

CREATE VIEW IF NOT EXISTS v_open_positions AS
SELECT symbol, side, qty, entry_avg, mark, unrealized, sl_price, tp_prices_json, ratchet_stage, plan_id
FROM positions WHERE snapshot_ts=(SELECT MAX(snapshot_ts) FROM positions);

CREATE VIEW IF NOT EXISTS v_open_orders AS
SELECT order_id, client_oid, symbol, side, type, price, qty, status, purpose FROM orders WHERE status IN ('new','partially_filled');

CREATE VIEW IF NOT EXISTS v_exposure AS
SELECT p.symbol, u.grp, p.qty*p.mark AS notional,
       (p.qty*p.mark)/(SELECT equity FROM equity_curve ORDER BY ts DESC LIMIT 1) AS notional_x
FROM v_open_positions p LEFT JOIN v_universe_active u ON u.symbol=p.symbol;

CREATE VIEW IF NOT EXISTS v_equity_daily AS
SELECT date(ts,'unixepoch') AS d, MAX(equity) AS high, MIN(equity) AS low,
       (SELECT equity FROM equity_curve e2 WHERE date(e2.ts,'unixepoch')=date(e.ts,'unixepoch') ORDER BY ts DESC LIMIT 1) AS close
FROM equity_curve e GROUP BY d ORDER BY d DESC LIMIT 400;

CREATE VIEW IF NOT EXISTS v_today_pnl AS
SELECT (SELECT equity FROM equity_curve ORDER BY ts DESC LIMIT 1) -
       (SELECT close FROM v_equity_daily WHERE d=date('now','-1 day')) AS pnl_today;

-- ── 稽核與績效 ─────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_trade_journal AS SELECT * FROM trade_journal;
CREATE VIEW IF NOT EXISTS v_trades_closed AS
SELECT trade_id, symbol, direction, setup_type, r_net, mae_r, mfe_r, hold_hours, exit_reason, stop_reason FROM trade_journal;
CREATE VIEW IF NOT EXISTS v_trade_plans_full AS SELECT * FROM trade_plan;
CREATE VIEW IF NOT EXISTS v_backtest_history AS
SELECT change_id, strategy_version, metrics_json, acceptance_pass, ingest_ts FROM backtest_reports;
CREATE VIEW IF NOT EXISTS v_perf_summary AS
SELECT COUNT(*) AS n, AVG(r_net) AS expectancy,
       AVG(CASE WHEN r_net>0.1 THEN 1.0 ELSE 0.0 END) AS win_rate FROM trade_journal;
-- 可對外公開的績效：只有 AUDIT 簽發的月報，無單筆細節
CREATE VIEW IF NOT EXISTS v_perf_public AS
SELECT period, n_trades, win_rate, expectancy, max_dd, signed_by, metrics_version
FROM perf_reports WHERE published=1;

-- ── 行銷 ───────────────────────────────────────────────────
-- CREATIVE 只拿得到「可公開的盤面描述」：方向與結構，無進場價、止損、倉位
CREATE VIEW IF NOT EXISTS v_public_context AS
SELECT symbol, date, htf_bias,
       json_extract(context_json,'$.structure') AS structure,
       json_extract(context_json,'$.key_zones_public') AS key_zones
FROM htf_context;

CREATE VIEW IF NOT EXISTS v_content_pipeline AS
SELECT content_id, pillar, format, status, scheduled_for, approver FROM content;
CREATE VIEW IF NOT EXISTS v_content_metrics AS
SELECT content_id, pillar, published_ts, permalink, metrics_24h_json, metrics_7d_json FROM content WHERE status='PUBLISHED';
CREATE VIEW IF NOT EXISTS v_ig_insights_daily AS SELECT * FROM ig_insights ORDER BY date DESC LIMIT 400;

-- ── 維運 ───────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_agent_status AS
SELECT agent_id, MAX(ts) AS last_seen, task, status, error FROM agent_heartbeat GROUP BY agent_id;
CREATE VIEW IF NOT EXISTS v_llm_usage AS
SELECT date(ts,'unixepoch') AS d, agent_id, model, COUNT(*) AS calls,
       SUM(input_tokens) AS in_tok, SUM(output_tokens) AS out_tok
FROM llm_usage GROUP BY d, agent_id, model;
CREATE VIEW IF NOT EXISTS v_backup_status AS SELECT date, backup_ok, restore_test_ok, path FROM backups ORDER BY date DESC LIMIT 90;
CREATE VIEW IF NOT EXISTS v_row_counts AS SELECT table_name, row_count, merkle_root, date FROM audit_anchor ORDER BY date DESC LIMIT 60;
CREATE VIEW IF NOT EXISTS v_audit_anchor AS SELECT * FROM audit_anchor ORDER BY date DESC LIMIT 60;
CREATE VIEW IF NOT EXISTS v_bug_reports AS SELECT bug_id, reporter, agent_id, skill_name, severity, symptom, status, ingest_ts FROM bug_reports;
-- 記憶治理：只有 VALIDATED / PROMOTED 的知識可以被分析類 Agent 引用
CREATE VIEW IF NOT EXISTS v_knowledge_validated AS
SELECT knowledge_id, domain, claim, status, sample_n, validated_by, promoted_to FROM knowledge
WHERE status IN ('VALIDATED','PROMOTED');
-- 未驗證的線索只給 LAB 與 REDTEAM（他們的工作就是去驗證或推翻）
CREATE VIEW IF NOT EXISTS v_knowledge_unverified AS
SELECT knowledge_id, source_agent, domain, claim, evidence_json, sample_n, ingest_ts FROM knowledge
WHERE status='UNVERIFIED';
-- 失敗歸因到 skill：哪個 skill 最常壞
CREATE VIEW IF NOT EXISTS v_skill_failures AS
SELECT skill_name, agent_id, COUNT(*) AS n, MAX(ingest_ts) AS last_seen
FROM bug_reports WHERE skill_name IS NOT NULL GROUP BY skill_name, agent_id ORDER BY n DESC;
CREATE VIEW IF NOT EXISTS v_fix_log AS SELECT bug_id, commit_hash, reviewer, approved_by, deployed_ts FROM fix_log;
CREATE VIEW IF NOT EXISTS v_task_board AS SELECT task_id, assignee, status, score, ts FROM tasks;
