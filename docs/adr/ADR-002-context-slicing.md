# ADR-002：知識分發用「單一真相 + 生成式角色切片」

狀態：**採納** · 日期 2026-09-09 · 取代了「每個 Agent `@import` 完整 shared/」

## 背景
15 個 Agent 需要共享規則（一致性），但每個 Agent 只該知道自己職責範圍內的條款（隔離）。

## 選項
| 方案 | 一致性 | 隔離 | token | 維護 |
|---|---|---|---|---|
| A. 每個 Agent 複製一份規格 | ✗ 必然漂移 | ✓ | 差 | 差 |
| B. 全部 `@import` 同一份 `shared/` | ✓ | ✗ 認知混淆 | 差 | 好 |
| C. 單一真相 + 生成切片（`build_context.py`） | ✓ 雜湊驗證 | ✓ 逐節裁切 | 好 | 中（多一個生成步驟） |
| D. 做成 MCP server，Agent 用工具查詢規則 | ✓ | ✓ | 好 | 差（多一個服務） |

## 決定
選 **C**。憲法（`CONSTITUTION.md`）逐字複製進每個切片（全體必須一致的東西不隔離）；其餘依 `context_map.yaml` 逐節裁切。

關鍵設計：`RISK_RULES.md` 刻意分成 **A 節（提案要件）** 與 **G 節（Gate 門檻）**。CHART 只拿到 A 節——它不該看到門檻數值，否則會把分析優化成「剛好通過檢查」（Goodhart 定律）。

## 後果
- 改 `shared/` 後**必須**跑 `build_context.py`，否則 Agent 停工（這是設計，不是 bug）。
- 多了 `context_map.yaml` 要維護；`lint_agents.py` 會檢查涵蓋率。
- CHART 的規則 context 從 6.7 KB 降到 2.2 KB。

## 何時重新考慮
Agent 數量 > 25，或需要語意檢索（而非逐節裁切）時，改採 D。
