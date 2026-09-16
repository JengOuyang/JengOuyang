# docs/adr/ — 架構決策紀錄（Architecture Decision Records）

每個檔案記錄一個決定：背景 → 選項 → 決定 → 後果 → 何時該重新考慮。

命名：`ADR-<三位數>-<英文短語>.md`。已做的決定不刪除、不改寫；改變主意就寫新的 ADR 並在舊的標記 `Superseded by ADR-XXX`。

| 編號 | 決定 |
|---|---|
| ADR-001 | 用自寫 Discord Router + `claude -p`，而不是官方 Channels plugin |
| ADR-002 | 知識分發用「單一真相 + 生成式角色切片」，而不是共享 import |
| ADR-003 | 資料權限做在視圖層，而不是 prompt 約束 |
| ADR-004 | 開發工作區 `dev/` 與 Agent 運行區 `agents/` 分離 |
