# router/ — Discord Router — 系統的心臟

常駐 Python 程式，同時登入 16 隻 Discord Bot，把訊息路由到對應的 Agent。

| 檔案 | 作用 |
|---|---|
| `discord_router.py` | 主程式：Gateway 連線、佇列、`claude -p` 呼叫、排程、狀態表情、額度控制 |
| `agents.yaml` | 每個 Agent 的 Bot token 變數、模型、工具白名單、程式對照、Owner 指令 |
| `scheduler.yaml` | 45 個排程；到點時以 Discord 訊息 `[CRON:job] @Agent` 觸發（所有觸發留紀錄） |
| `.env` | 所有金鑰（Bot token、Bitget、Meta、頻道 ID）— **不進 git**，NTFS 權限只給自己 |
| `.env.example` | 範本，複製為 `.env` 後填寫 |
| `mcp_canva.json` | CREATIVE 用的 Canva MCP 設定 |
| `requirements.txt` | Python 套件 |
| `start.ps1` | 手動前景啟動（測試用） |
| `watchdog.ps1` | 工作排程器每 5 分鐘檢查，掛了就重啟 |
| `router_state.db` | 本機狀態：thread↔session 對應、呼叫計數、心跳（**不是**正式資料倉） |

啟動時會先跑 preflight（上下文完整性 + Agent 定義 lint），不通過就不啟動。
