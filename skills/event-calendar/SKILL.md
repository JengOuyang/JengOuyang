---
name: event-calendar
description: 維護高影響事件日曆（總經事件、財報、休市、COMEX 時段）供 RISK G7/G8/G14 使用
---

# event-calendar

## 何時使用
維護高影響事件日曆（總經事件、財報、休市、COMEX 時段）供 RISK G7/G8/G14 使用。

## 輸入 / 輸出契約
- **輸入**：Fed/BLS/NYSE/CME/公司 IR 的行事曆
- **輸出**：`data/calendar/events.json`：`{event, ts_utc, ts_taipei, impact, affects[]}`
- **失敗時**：來源不可用就保留舊資料並告警——空的事件日曆會讓 RISK 放行不該放行的單

## 步驟
1. 來源：Fed 行事曆、BLS、BEA、NYSE 假日表、公司 IR 財報日、CME/COMEX 交易時段。
2. 寫入 data/calendar/events.json：{event, ts_utc, ts_taipei, impact, affects[]}。
3. 未來 30 天；每日更新；HIGH 事件前 2 小時由程式發 EVENT_WARNING。

## 完成檢查
- [ ] 時間雙標（UTC + 台北）
- [ ] affects 正確標層

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `scripts/calendar_update.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
