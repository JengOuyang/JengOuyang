---
name: ratchet-management
description: 棘輪止盈止損管理（R1–R4、RH）
---

# ratchet-management

## 何時使用
棘輪止盈止損管理（R1–R4、RH）。

## 輸入 / 輸出契約
- **輸入**：目前部位、未實現 R、1H swing、ATR
- **輸出**：新的 SL 價位與棘輪階段（R0–R4/RH）
- **失敗時**：計算出的新 SL 比現有 SL 不利 → 不動作（棘輪只前進不後退）

## 步驟
1. +1R → SL 保本；TP1(+2R) 平 40% → SL +0.5R；之後 SL = max(SL, min(1H swing − 0.3 ATR, close − 3 ATR))；TP2(+3R) 平 30%；TP3(+5R)。
2. 只前進不後退。
3. hedge_lock（預設關閉）：EVENT_WARNING 且 ≥ +1R 時開等量反向鎖利。

## 完成檢查
- [ ] SL 單調
- [ ] 階段寫入 positions.ratchet_stage

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `engine/ratchet.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
