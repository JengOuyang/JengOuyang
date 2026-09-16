# docs/ — 給人讀的文件

| 檔案 | 內容 | 何時看 |
|---|---|---|
| `DAY0_RUNBOOK.md` | **Day 0 逐步操作手冊**：14 步（含步驟 0 選 WSL2、步驟 3B 接 GitHub），每個指令標明【PowerShell】／【瀏覽器】／【記事本】／【Discord】、整塊複製、預期輸出、失敗處置 | 第一天，照著做 |
| `QUICKSTART.md`（在根目錄） | 30 分鐘濃縮版 | 已熟悉環境時 |
| `00_WHITEPAPER.md` | 白皮書總綱：問題陳述、替代方案、團隊、商品、風控、經濟、威脅模型、終止條件 | 第一次來 / 要跟別人解釋這是什麼 |
| `01_ARCHITECTURE.md` | 架構與理由：四層知識模型、隔離機制、資料流 | 要改架構、或想知道「為什麼這樣設計」 |
| `02_SETUP_GUIDE.md` | 手把手安裝：Windows → Claude Code → Bot → Router | 第一次建置（完整版） |
| `03_DISCORD_SETUP.md` | Discord 伺服器、18 個頻道、16 隻 Bot 對照表 | 建 Discord 時 |
| `04_DEV_ENVIRONMENT.md` | **你的開發環境怎麼設**、為什麼開發不會污染 Agent | 開始寫程式前必讀 |
| `05_OPERATIONS.md` | 日常維運、交易日邊界、故障排除、災難情境、`system_state` 狀態機 | 系統上線後 |
| `06_ROADMAP.md` | 8 週里程碑與驗收標準 | 規劃進度 |
| `07_GLOSSARY.md` | 術語表（SMC / OB / FVG / MSS / R / Kelly / 棘輪 / 型態學…） | 看不懂某個詞 |
| `08_BUILD_PLAN.md` | **Day 0 分界線 + 建置待辦（唯一真相）**：CEO 從這裡取任務 | 系統還沒完工時，每天 |
| `09_HARNESS_LESSONS.md` | 別人踩過的坑對照本專案：改了什麼、哪些刻意不改 | 想調整 Agent 協作機制之前 |
| `10_CODE_GOVERNANCE.md` | **版控、備份三層、汙染防治、金鑰治理、回滾** | AI 開始改你的程式之後 |
| `11_LEGACY_ASSETS.md` | 既有專案資產索引與能力對照表（由 `scan_legacy.py --all` 生成） | 移植舊專案時 |
| `CHANGELOG.md` | 各版改了什麼、為什麼改（多半是真實失誤的紀錄） | 想知道「這個機制為什麼存在」 |
| `adr/` | 架構決策紀錄：每個重要選擇的理由與被否決的方案 | 想推翻某個決定之前 |
| `TRADE-DESK_whitepaper.html` | 上述文件的互動版（15 個分頁，深色主題） | 想一次瀏覽全部 |
| `12_DIGITAL_BOUNDARY.md` | **Agent 的數位邊界**：四層防線（L0 OS 沙箱／L1 工具層／L2 worktree／L3 偵測）、外部實務對照、為什麼必須跑在 WSL2 | 設定權限、懷疑越權時 |
| `13_GITHUB.md` | **GitHub 用法與備份**：要不要用、用哪三件事、Free 方案私有庫少了什麼、3-2-1 備份 | Day 0 建版控時、每週備份時 |

新增文件的規則：編號遞增、檔名全大寫、開頭寫「這份文件回答什麼問題」。
**文件裡的數字（視圖數、排程數、lint 項數…）由 `scripts/verify_docs_claims.py` 驗證**，不要手改——改了 lint 第 15 項會擋下。
