---
name: legacy-port
description: FORGE/LAB 把既有專案的既成程式移植進 TRADE-DESK 時使用（只讀被指派的檔、符合三層分離、附驗證）
---

# legacy-port

## 何時使用
CEO 指派了 `docs/11_LEGACY_ASSETS.md` 裡標記為 `PORT` 的項目時使用。
**只有被指派的那幾個檔可以讀**——不要為了「先了解一下」去讀整個舊專案。

## 輸入 / 輸出契約
- **輸入**：`TASK_ASSIGN` 指定的 `legacy_paths[]`、對應的 `shared/` 規格、`legacy/inventory.json`
- **輸出**：新檔案 + 測試 + `FIX_PROPOSAL` 格式的移植報告（含 `verify_delivery_output`）
- **失敗時**：舊程式與本專案的架構原則衝突且無法調整 → 回報 `REJECTED` 並說明衝突點，**不要「先照抄再說」**

## 步驟

1. **只讀被指派的檔**。讀完先寫一段「這支程式實際做了什麼」，與舊專案的文件說法對照——文件常常是舊的，程式才是事實。
2. **三層分離檢查**（最常見的移植衝突）：舊專案多半是「一支程式從分析到下單一路做完」。移植時必須拆開：
   - 分析判斷 → 這是 LLM Agent 的職責，程式只提供數值化特徵
   - 風控檢查 → 必須走 `engine/risk_gate.py`，不得在採集或下單程式裡自己判斷
   - 下單 → 只能在 `engine/executor.py`，且金鑰只從 `.env` 讀
3. **資料寫入口檢查**：舊程式若直接寫資料庫，改成走本專案的 ingest 管道（append-only + hash chain）。這一條沒有例外。
4. **清金鑰**：`scan_legacy.py` 標記 `has_secrets` 的檔案，硬編碼的 key 一律改成環境變數，並確認舊值不會被 commit。
5. **保留可用的東西，丟掉黏著劑**：值得複用的通常是「已經被市場驗證過」的部分——參數、邊界條件、重試與限流邏輯、交易所 API 的實際回應處理。不值得複用的是舊專案的框架、路由、設定載入方式。
6. **寫測試再宣稱完成**：至少一個 happy path + 一個舊專案踩過的邊界（限流、斷線、部分成交）。
7. **跑 `python ../../scripts/verify_delivery.py`**，把輸出附在 `FIX_PROPOSAL` 裡。我不替自己打分數（憲法第八條）。

## 完成檢查
- [ ] 只讀了被指派的檔
- [ ] 沒有任何硬編碼金鑰
- [ ] 分析／風控／執行三層沒有混在同一支程式
- [ ] 資料寫入走 ingest 管道
- [ ] 測試通過且輸出已附上
- [ ] 移植報告寫明「保留什麼、丟掉什麼、為什麼」

## 相關程式
- `scripts/scan_legacy.py`（盤點）
- `scripts/verify_delivery.py`（獨立驗收）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 即可使用。
