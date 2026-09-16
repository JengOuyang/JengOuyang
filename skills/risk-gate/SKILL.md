---
name: risk-gate
description: RISK Gate 程式規格與解釋（A1–A14、C1–C8、D、E）
---

# risk-gate

## 何時使用
RISK Gate 程式規格與解釋（A1–A14、C1–C8、D、E）。

## 輸入 / 輸出契約
- **輸入**：一份 TradePlan + 帳戶狀態 + strategy_params
- **輸出**：`RISK_DECISION{approved, reasons[{code, rule, detail}]}`
- **失敗時**：Gate 程式本身異常 → **預設拒絕所有單**並 BUG_REPORT，絕不預設放行

## 步驟
1. 逐條檢查 RISK_RULES A1–A14；任一不過 → REJECTED + reasons[規則編號 + 數值]。
2. 帳戶級 C1–C8 每 5 分鐘。
3. 解釋時附算式。
4. 規則變更只能經 config_versions。

## 完成檢查
- [ ] reasons 有規則編號
- [ ] params_version 正確

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- `engine/risk_gate.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
