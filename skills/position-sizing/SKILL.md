---
name: position-sizing
description: 計算倉位（1.5%/1.0% 上限、½ Kelly、EV）時使用
---

# position-sizing

## 何時使用
計算倉位（1.5%/1.0% 上限、½ Kelly、EV）時使用。

## 輸入 / 輸出契約
- **輸入**：`{p, R, equity, entry, stop_loss, tier}`
- **輸出**：`{risk_pct, risk_amount, qty, leverage}` + 完整算式
- **失敗時**：qty < min_qty 或超過曝險上限 → 拒絕，不要四捨五入硬湊

## 步驟
1. p = rolling_winrate(setup_type)（<30 筆用 0.40）；R = plan.rr；kelly_f = p − (1−p)/R。
2. risk_pct = min(cap, max(0, kelly_f) × 0.5)；cap = 1.5%（T2 1.0%）。
3. qty = equity × risk_pct ÷ |entry − SL|，依合約 step 取整；leverage = ceil(notional ÷ (equity × 10%))，上限 10x。
4. EV = p×R − (1−p) ≥ 0.15。

## 完成檢查
- [ ] 算式列出
- [ ] qty ≥ min_qty

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- （純知識型技能，無程式）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
