---
name: data-readonly
description: 任何 LLM Agent 需要查資料倉時使用；只允許唯讀 SQL
---

# data-readonly

## 何時使用
任何 LLM Agent 需要查資料倉時使用；只允許唯讀 SQL。

## 輸入 / 輸出契約
- **輸入**：一句 SELECT/WITH 查詢
- **輸出**：`{agent, rows, count, truncated}` JSON
- **失敗時**：未授權或非 SELECT 一律拒絕；需要新視圖發 SKILL_REQUEST 給 FORGE

## 步驟
1. 用 `python scripts/query_readonly.py "<SQL>"`（PRAGMA query_only=1，只接受 SELECT/WITH）。
2. 優先用視圖：v_latest_ohlcv、v_latest_indicators、v_open_positions、v_today_pnl、v_setup_winrates、v_agent_status、v_universe_active。
3. 結果超過 200 列請加 LIMIT 或聚合。
4. 看到 suspect=1 的資料要在回覆中註明。

## 完成檢查
- [ ] 沒有 INSERT/UPDATE/DELETE
- [ ] 查詢附在回覆的 artifacts 或 reasoning 中

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/query_readonly.py（附範例實作）`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
