# 開發筆記（NOTES.md）

> 給「開發者助理」的專案背景。這裡只放**穩定**的事實與決策；一次性的待辦寫 `TASKS.md`。
> 不要把任何 Agent 的人設或規則抄到這裡——那些的唯一真相在 `../shared/`。

## 技術決策速查
| 決策 | 結論 | 出處 |
|---|---|---|
| Agent 執行方式 | Router 以 `claude -p` 在 `agents/<id>/` 啟動，非官方 Channels plugin | ADR-001 |
| 知識分發 | `shared/` 單一真相 → `build_context.py` 生成角色切片 → `.context/` | ADR-002 |
| 資料存取 | LLM 只能查視圖，授權在 `shared/view_grants.yaml`，強制在 `query_readonly.py` | ADR-003 |
| 開發／運行分離 | `dev/` 不在 `agents/` 繼承鏈上 | ADR-004 |
| 交易執行 | LLM 只提案；`engine/risk_gate.py` 與 `engine/executor.py` 是唯一碰錢的程式 | 白皮書 §2.2 |

## 環境
- 根目錄 `C:\trade-desk`，虛擬環境 `.venv`
- Python 3.12、Node LTS（Claude Code 需要）、Git
- `router/.env` 存所有金鑰（NTFS 權限只給自己，不進 git）
- Router 由 Windows 工作排程器登入時啟動，`watchdog.ps1` 每 5 分鐘檢查

## 已知的坑
- `~/.claude/CLAUDE.md`（使用者層）會被**所有** Agent 繼承。不要在那裡放個人開發偏好。
- Claude Code 的 `--resume` 綁 session id，存在 `router/router_state.db` 的 `sessions` 表；thread 刪掉後那筆會變孤兒，不影響運作。
- SQLite 在 WAL 模式下多程序讀寫沒問題，但備份要用 `.backup` 而不是複製檔案。
- Bitget 幣股／黃金永續與 BTC 同屬 `productType=USDT-FUTURES`，但合約面值與精度不同，一律查 `/api/v2/mix/market/contracts`。

## 待確認（實作時要驗證的假設）
- [ ] Windows 未登入狀態下 `claude -p` 能否讀到 OAuth 憑證（影響 Router 常駐設定）
- [ ] Claude Pro 的 5 小時窗實際可支撐的 `claude -p` 次數（WATCH 上線後用實測數據修正白皮書 §11）
- [ ] Bitget Demo Trading 的幣股／貴金屬標的是否齊全
