---
name: data-integrity
description: LEDGER/FEED/EXEC 寫入資料倉、hash chain、Merkle 錨點、備份時使用
---

# data-integrity

## 何時使用
LEDGER/FEED/EXEC 寫入資料倉、hash chain、Merkle 錨點、備份時使用。

## 輸入 / 輸出契約
- **輸入**：待寫入的資料列 + 前一列的 row_hash
- **輸出**：`{row_id, row_hash}`；每日 Merkle root
- **失敗時**：chain 驗證失敗 → 立即 P0 告警並停開新單，不自行修復

## 步驟
1. row_hash = sha256(prev_hash + canonical_json(row))；canonical = 鍵排序、無空白、UTF-8。
2. 每日 Merkle root 貼 #audit-log 並寫 audit_anchor。
3. 更正只新增 corrections。
4. 備份 + 每週還原測試。

## 完成檢查
- [ ] chain 驗證通過
- [ ] 備份可還原

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `engine/ingest_server.py`
- `scripts/merkle_anchor.py`
- `scripts/backup.py`
- `scripts/verify_chain.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
