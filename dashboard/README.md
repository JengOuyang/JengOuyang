# dashboard/ — 戰情室（WATCH 的工作區）

FastAPI + WebSocket + 單頁深色 HTML，綁 `127.0.0.1:8080`（或 Tailscale 內網），**不開公網**。

| 檔案 | 內容 |
|---|---|
| `app.py` | REST + WebSocket；只讀資料倉視圖，不碰交易所金鑰 |
| `static/index.html` | 單頁：KPI 列、資產曲線、持倉／掛單／已關單、15 張 Agent 卡片、行銷欄、額度條、告警 |
| `reports/` 路由 | `GET /reports/<type>/<id>` 提供 Agent 產出的互動式 HTML 報告（見 `skills/report-preview`）。長報告不貼進 Discord，只貼連結——這是為了讓 Blacksheep 真的會看完。 |

只有兩個按鈕：`PAUSE NEW ENTRIES`、`FLATTEN ALL`，都要二次確認並寫入紀錄。
