# 01 — 架構與理由

> 這份文件回答：**「為什麼是這樣設計的？」** 每個決定的取捨、被否決的替代方案、以及什麼情況下該重新考慮。
> 想知道「怎麼做」看 `02_SETUP_GUIDE.md`；想知道「做什麼」看 `00_WHITEPAPER.md`。

## 1. 核心命題

一個由 15 個 LLM Agent 組成、會碰真錢的系統，有三個必須同時成立卻互相拉扯的需求：

| 需求 | 如果只顧這個會怎樣 |
|---|---|
| **知識共享**：全隊對規則、資料、術語的理解必須一致 | 每個 Agent 載入全部知識 → 認知混淆、token 爆炸 |
| **認知隔離**：每個 Agent 只該知道自己職責範圍內的事 | 完全隔離 → 規格複製漂移、無法協作 |
| **不互相干擾**：15 個並行的 process 不能踩到彼此 | 過度上鎖 → 系統動不了 |

TRADE-DESK 的答案：**不要用「檔案放哪」解決這三件事，用「知識以什麼方式到達 Agent」解決。**

## 2. 四層知識模型

這是整個架構的核心。任何一項知識，先問「它屬於哪一層」，答案就決定了它怎麼儲存、怎麼傳遞、怎麼隔離。

| 層 | 內容 | 到達方式 | 隔離手段 | 實作 |
|---|---|---|---|---|
| **憲法** | 九條鐵律、人類保留權限、身分邊界 | **必須**在 context | 不隔離——全體逐字一致才是目的 | `shared/CONSTITUTION.md` → 複製進每個 `.context/` |
| **角色規則** | 該角色適用的條款 | 在 context，但**只有自己那份** | 從單一真相「生成切片」 | `context_map.yaml` + `build_context.py` → `.context/` |
| **事實知識** | 行情、指標、歷史、其他 Agent 的產出 | **不進 context**，用查詢 | 資料庫視圖 + 授權矩陣 | `view_grants.yaml` + `db/002_views.sql` + `query_readonly.py` |
| **交接資訊** | Agent 之間傳的東西 | 只走 Discord 的 JSON | 通道唯一、schema 驗證、方向明確 | `shared/PROTOCOL.md` + `shared/schemas/` |

### 2.1 為什麼「角色規則」要用生成的，不用 import

最直覺的做法是每個 Agent 的 `CLAUDE.md` 寫 `@../../shared/RISK_RULES.md`。這會出三個問題：

1. **認知混淆**：CHART 只需要知道「什麼樣的提案會被接受」（A 節），但它讀到了帳戶熔斷（C 節）、執行規則（D 節）、棘輪（E 節）。它會開始推理不屬於它的事，甚至在提案裡討論倉位大小——那是 RISK 的職責。
2. **Goodhart 定律**：如果 CHART 看到「G5：RR ≥ 2.0」，它會把 TP 拉到剛好 RR = 2.0 來通過檢查，**優化通過率而不是優化交易品質**。所以 G 節的門檻數值它根本不該看到；被退件時只給理由「類別」（`RR_INSUFFICIENT`），不給數值。
3. **token**：整份 `RISK_RULES.md` 約 6.7 KB，CHART 實際需要的 A 節只有 2.2 KB。乘以每天數十次呼叫，在 Claude Pro 的額度下是真金白銀。

生成式切片同時解決三者，而且來源仍然只有一份：

```
shared/RISK_RULES.md  ──build_context.py──┬─► agents/chart/.context/rules.md   （A 節，2.2 KB）
     （唯一真相）        依 context_map.yaml  ├─► agents/risk/.context/rules.md    （全文，6.7 KB）
                                            └─► agents/creative/.context/rules.md（零風控條款）
```

### 2.2 防漂移：雜湊驗證

生成物最大的風險是「來源改了、切片沒重建」。每個切片檔頭帶來源的 SHA-256，`.context/MANIFEST.json` 記錄全部來源雜湊：

- `python scripts/build_context.py --verify` 重算並比對
- Router 啟動時跑 preflight，不通過就**不啟動**
- Agent 的憲法第六條規定：驗證失敗就停工，回 `PROTOCOL_ERROR` 並 @FORGE
- `lint_agents.py` 也含這項檢查

所以「規格漂移」在這個系統裡不是「以後才發現的 bug」，而是「立刻停機的事故」。

### 2.3 事實知識為什麼不進 context

行情、歷史交易、其他 Agent 的產出是**動態且龐大**的。塞進 context 會遇到：載入時已過期、量大到吃掉整個視窗、而且**無法做權限控制**（進了 context 就全看得到）。

改成查詢後，權限可以做在視圖層：

| Agent | 看得到 | 看不到 | 為什麼 |
|---|---|---|---|
| REDTEAM | `v_blind_plan`（剔除 reasoning 與 confidence） | CHART 的推理 | 看到推理就不是盲審 |
| CHART | `v_reject_categories`（只有理由代碼） | G 節門檻數值 | 防 Goodhart |
| CREATIVE | `v_public_context`（方向與結構） | 進場價、止損、倉位 | 防止在 IG 洩漏可交易資訊 |
| GROWTH | 只有內容與 IG 數據 | 全部交易資料 | 職責無關 |

這是**物理隔離**（`query_readonly.py` 會拒絕未授權的視圖，且完全禁止查底層資料表），不是 prompt 上的勸告。

## 3. 執行架構：Router + `claude -p`

### 3.1 為什麼不用官方的 Channels plugin

Claude Code 官方支援把 Discord 訊息推進一個「正在開著的」session。但一個 session 對應一隻 Bot、必須保持互動視窗開啟，15 個 Agent 就得開 15 個視窗，且無法控制佇列、額度與並行度。

Router 的做法是：持有 16 隻 Bot 的 Gateway 連線，收到 @mention 就在對應 Agent 的目錄執行 `claude -p`。代價是失去互動式的即時串流（但我們用 👀 / ⚙️ / ✅ / ❌ 的表情回饋補上），換到的是佇列、額度控制、排程、狀態機與稽核紀錄。詳見 `adr/ADR-001`。

### 3.2 三層分離（不變的鐵律）

```
思考層（LLM）   → 讀資料、分析、提案、審核、寫程式
     ↓ TradePlan(JSON)
閘門層（程式）   → RISK Gate：規則驗證、倉位計算、否決
     ↓ ApprovedOrder(JSON)
執行層（程式）   → EXEC：下單、止損、棘輪、對帳
```

任何 LLM Agent 都碰不到交易所私鑰、碰不到 Meta token、不能寫入資料倉。LLM 會幻覺、會被誘導、會算錯小數點；程式不會。

### 3.3 抗身分漂移的三個機制

長 thread 裡灌入大量他人輸出後，Agent 可能逐漸偏離角色。對策：

1. **尾端重貼角色**：Router 在每則 prompt 的**最後**附上 `<role_reminder>`（近因效應比開頭的系統提示更強）
2. **session 輪替**：同一 thread 超過 20 輪就強制開新 session，只靠 `thread_history` 帶脈絡
3. **REDTEAM 常駐 stateless**：盲審不帶任何 thread 記憶

## 4. 記憶三態（以及被禁止的第四態）

| 型態 | 存在哪裡 | 生命週期 |
|---|---|---|
| 情節記憶 | Claude session（`--resume`） | 單一 Discord thread |
| 語意記憶 | 資料倉（查詢取得） | 永久，可稽核 |
| 程序記憶 | `skills/<name>/SKILL.md` | 永久，可跨專案搬遷 |
| ~~自我修改的人設~~ | ~~`PERSONA.md`~~ | **禁止** |

第四種是最常見也最危險的做法：讓 Agent 把「學到的經驗」寫回自己的人設。它不可稽核、會累積偏誤、且兩個月後沒人知道為什麼這個 Agent 變成這樣。長期知識的唯一去處是資料倉，或由 FORGE 提案、Owner 核准後進入 `shared/`。

## 5. 併發與干擾

| 干擾類型 | 解法 |
|---|---|
| 兩個任務同時給同一個 Agent | Router 每 Agent 佇列並行度 = 1 |
| 太多 LLM 同時跑（額度） | 全域 semaphore = 3；每 Agent 每小時上限；額度低自動延後 CMO/GROWTH/LAB |
| 同時寫同一個檔案 | 只有 `ingest_server.py` 能寫資料倉；Agent 產出只寫自己的 `outbox/` |
| 開發時改到運行中的程式 | DEMO 模式或 `!pause`；大改動用 git worktree |
| Agent 互相無限 @ | 訊息帶 `hop`，≥ 6 停止並 @CEO |
| 開發 session 與 Agent 互相污染 | `dev/` 不在 `agents/` 繼承鏈上（見 `04_DEV_ENVIRONMENT.md`） |
| Agent 互相客套聊不完 | `NO_REPLY` + a2a 5 輪上限 |
| thread 把頻道塞爆 | 依頻道分層的自動封存（60/1440/4320/10080 分鐘） |
| Discord 權限缺失造成靜默失敗 | Router 開機檢查 16 隻 Bot 的 9 項權限，缺就拒絕啟動 |

## 5.5 Harness Engineering：三根支柱

「Harness 比 model 重要」不是口號——Terminal Bench 2.0 用**相同模型**但更好的架構提升了 14 個百分點，CORE-Bench 從 42% 跳到 95%。我們把力氣花在下面三件事，而不是換更大的模型。

### 支柱一：評估迴路（你不能讓一個人自己幫自己打分數）
| 被評估者 | 評估者 | 機制 |
|---|---|---|
| CHART 的分析 | REDTEAM | 盲審（拿不到 reasoning 與 confidence） |
| LAB 的回測 | REDTEAM | `--verify` 重跑，固定 seed 與資料版本 |
| FORGE 的交付 | CEO / REDTEAM | **`scripts/verify_delivery.py` 自己跑測試**，不採信交付者貼的輸出 |
| 實盤績效 | AUDIT | 統一量尺 + DRIFT_ALERT |
| Agent 定義自洽 | 程式 | `lint_agents.py`（33 項）+ Router preflight |
| 上下文一致 | 程式 | SHA-256 + `build_context.py --verify` |

### 支柱二：架構約束（用結構而非紀律）
- 資料權限做在**視圖層**，不是 prompt（41 個視圖 + 授權矩陣 + 查詢時強制）
- 角色規則做在**生成的切片**，不是「請不要看」
- 依賴方向由 lint 強制：`engine/` 不得 import `agents/`；沒有 Agent 能被授權寫 `data/`
- 迴圈保護由 **Router 記帳**，不是 LLM 自報 hop

### 支柱三：記憶治理（未驗證的東西不能當知識）
`knowledge` 表的三階段 `UNVERIFIED → VALIDATED → PROMOTED`，隔離做在視圖層：`v_knowledge_unverified` 只授權給 LAB 與 REDTEAM（他們的工作就是去驗證或推翻它）。CHART 想引用未驗證的線索也拿不到。

### 四個生產級驗收標準
1. **評估精確度**：能指出哪個 **skill** 失敗與為什麼（`bug_reports.skill_name` + `v_skill_failures`）
2. **圖可讀性**：系統能用紙筆畫在一頁上
3. **錯誤隔離**：失敗侷限在 skill 邊界內（輸入/輸出契約）
4. **可升級性**：換掉單一 skill 不用重寫系統（`skills/` 可獨立複製替換）

## 5.6 多 Agent 對話的終止條件

研究指出 **41.8% 的多 Agent 系統失敗來自缺少終止條件**。我們有三道：

| 機制 | 上限 | 觸發後 |
|---|---|---|
| `hop`（鏈長度，Router 記帳） | 6 | 🛑 中止，要求 CEO 收斂 |
| `a2a_turns`（同 thread 內 Agent 來回輪數） | 5 | 🛑 升級給 Blacksheep 裁示 |
| `NO_REPLY`（無實質內容時的沉默） | — | 💤 不貼訊息，重置 a2a 計數 |

第三道特別重要：Agent 被訓練得友善，會對「謝謝」「收到」持續回應。沒有沉默機制，兩個有禮貌的 Agent 可以聊到額度用完。

## 6. 誠實的限制

- **「完全防堵」做不到**，也不該做——Agent 必須交換資訊才能協作。能做到的是「每條資訊都有明確的通道、schema 與方向，任何跨界都在 Discord 留下紀錄」。
- **唯一無法用機制擋的**：你自己在 thread 裡隨口跟某個 Agent 說了不該說的（例如告訴 CREATIVE 現在的持倉）。那要靠紀律。
- **Blacksheep 才是真正的瓶頸**：導入 AI 之後最常見的失敗不是 Agent 做不好，而是人被 15 個 Agent 的輸出淹沒，變得比以前更忙。所以 CEO 的第一 KPI 是「Blacksheep 每天 ≤ 15 分鐘」，長報告一律走 `report-preview` 產 HTML 貼連結，而不是把兩百行貼進 Discord。
- **REDTEAM 的多樣性是妥協**：只有 Claude 一種模型時，用「盲審 + opus + 對抗式立場」替代跨模型審核。這比同源同 prompt 好，但不等同真正的跨模型審核。將來若有第二個模型來源，這是第一個該補的地方。
- **切片機制增加維護成本**：多了 `build_context.py`、`context_map.yaml`、視圖定義、lint 規則。這是真實成本，但比「CHART 某天用錯規則提案而你三週後才發現」便宜太多。

## 7. 什麼時候該重新考慮這個架構

| 訊號 | 該考慮的改變 |
|---|---|
| `#agent-health` 每天出現 ⏳ 延後 | 升級 Claude Max 5x（設定完全不用改） |
| Agent 數量 > 25 | 把 `shared/` 改成 MCP server，權限在 server 端強制 |
| 需要多台機器 | Router 拆成訊息佇列（Redis）+ worker |
| 有第二個模型來源 | REDTEAM 換回真正的跨模型審核 |
| 資料量 > 50 GB | SQLite → TimescaleDB |
