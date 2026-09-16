---
name: report-preview
description: 把要給 Blacksheep 審核的長輸出（回測報告、週報、FIX_PROPOSAL、每日匯報）渲染成可互動 HTML 並在 Discord 貼連結時使用
---

# report-preview

## 何時使用
你的輸出**超過 40 行**、或包含需要對照的表格／流程／diff，而收件者是 Blacksheep。

理由很實際：一份兩百行的 Markdown 貼進 Discord，Blacksheep 會往後拖、拖到明天、然後失去實質審核。同樣的內容做成有分頁與摺疊的 HTML，四分鐘看得完，而且他會真的留下意見。**Markdown 是 Agent 之間的傳輸格式，HTML 是給人看的展示面板**——兩者都要，不是二選一。

## 輸入 / 輸出契約
- **輸入**：你已經產好的結構化資料（JSON / Markdown）+ 報告類型
- **輸出**：`reports/<type>/<id>.html`，以及 Discord 上的一行摘要 + 連結 `http://127.0.0.1:8080/reports/<type>/<id>`
- **失敗時**：渲染失敗就退回貼 Markdown 摘要（前 30 行）+ 附完整檔案，不要因為渲染問題而不交付

## 步驟
1. 先產出**結構化資料**（JSON），不要直接寫 HTML——資料是真相，HTML 只是視圖。
2. 呼叫 `python ../../scripts/render_report.py --type <backtest|weekly|fix|daily> --data <path.json>`。
3. 在 Discord 貼：**一行結論 + 3–5 個關鍵數字 + 連結**。不要把整份報告貼進 Discord。
4. 若有需要 Blacksheep 決定的事，在 Discord 訊息裡直接列出選項（他可能只看訊息不點連結）。
5. 同一份報告更新時用同一個 `<id>`，覆寫檔案，連結不變。

## 哪些輸出必須走這個技能
| 輸出 | 產出者 | 類型 |
|---|---|---|
| `BACKTEST_REPORT` | LAB | `backtest` |
| 止損解剖週報／月度績效 | AUDIT | `weekly` |
| `FIX_PROPOSAL`（含 diff） | FORGE | `fix` |
| 每日匯報／建置日報 | CEO | `daily` |
| `GROWTH_REPORT` | GROWTH | `weekly` |
| `MARKETING_PLAN` | CMO | `weekly` |

## 完成檢查
- [ ] 先有 JSON 才有 HTML
- [ ] Discord 訊息 ≤ 15 行，含連結
- [ ] 需要決定的事直接寫在 Discord 訊息裡，不藏在報告內
- [ ] 同一份報告更新時連結不變

## 相關程式
- `scripts/render_report.py`
- `dashboard/app.py`（提供 `/reports/<type>/<id>` 路由）
