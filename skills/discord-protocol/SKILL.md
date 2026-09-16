---
name: discord-protocol
description: 在 Discord 上以 TRADE-DESK 協定（一行摘要 + JSON、msg_type、@mention、thread、hop）回覆與派工時使用
---

# discord-protocol

## 何時使用
在 Discord 上以 TRADE-DESK 協定（一行摘要 + JSON、msg_type、@mention、thread、hop）回覆與派工時使用。

## 輸入 / 輸出契約
- **輸入**：被 @mention 的 Discord 訊息（含 `<router>` 標頭與 thread 前文）
- **輸出**：一行人話摘要 + 一個通過 `shared/schemas/message.schema.json` 的 JSON 區塊
- **失敗時**：格式不合就重寫，不要送出半成品；無實質內容則回 `NO_REPLY`

## 步驟
1. 讀 shared/PROTOCOL.md 取得 msg_type 與 payload 欄位。
2. 決定 to[]，在人話摘要中 @ 每一個收件 Agent（Router 以 @mention 觸發）。
3. 組 JSON：msg_type、msg_id（<type>_<YYYYMMDD>_<HHMM>_<slug>）、from、to、task_id、ts(UTC)、status、needs_review、payload。
4. 回覆放在同一 thread；超過 2000 字讓 Router 分段（不要自行截斷 JSON）。
5. 若看到 hop ≥ 5，不再 @ 其他 Agent，改 @CEO 收斂。

## 完成檢查
- [ ] msg_type 在 PROTOCOL 清單內
- [ ] JSON 可被 json.loads 解析
- [ ] to[] 與 @mention 一致
- [ ] 有 task_id 時最後一則是 TASK_DONE/PROGRESS

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- （純知識型技能，無程式）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
