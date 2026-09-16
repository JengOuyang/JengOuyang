# 09 — Harness 經驗內化

> 這份文件回答：**「別人踩過的坑，我們踩得到嗎？改了什麼？哪些刻意不改？」**
> 來源：hanamizuki.tw 的五篇實戰文章（2026）。以下每一條都標明我們的**實際狀態**，而不是抽象認同。

---

## 摘要：檢查結果

| # | 他的教訓 | 我們原本 | 處置 |
|---|---|---|---|
| 1 | 缺少終止條件是多 Agent 失敗主因（41.8%） | **有 bug**：hop 靠 LLM 自報，沒寫就重置 | 🔴 已修：Router 記帳 |
| 2 | Agent 對客套話無限回應 | 沒有沉默機制 | 🔴 已修：`NO_REPLY` |
| 3 | Agent 之間會聊不完 | 只有 hop，沒有輪數上限 | 🔴 已修：5 輪升級人類 |
| 4 | 每小時建 thread 會塞爆頻道 | 封存時間寫死 1440 | 🟠 已修：18 個頻道分層 |
| 5 | thread 標題醜到無法辨識 | 取訊息前 80 字 | 🟠 已修：程式產生標題 |
| 6 | 權限缺失造成靜默失敗（debug 兩小時） | 沒有檢查 | 🟠 已修：開機 preflight |
| 7 | 「不能讓一個人自己幫自己打分數」 | CEO 看 FORGE **自報**的測試結果 | 🔴 已修：`verify_delivery.py` |
| 8 | Skill 塞五件事 → 無法歸因失敗 | 3 個 skill 混了 4–5 件事 | 🟠 已修：拆成 8 個 + 契約 |
| 9 | 記憶治理：未驗證知識會污染下游 | 有禁止自改人設，但無成熟度分級 | 🟠 已修：三階段 + 視圖隔離 |
| 10 | 失敗要歸因到最小單位 | BUG_REPORT 只記 agent_id | 🟠 已修：加 `skill_name` |
| 11 | 兩百行 Markdown = 沒有人真的審核 | 所有報告都貼 Discord 純文字 | 🟠 已修：`report-preview` |
| 12 | 「有了 AI 反而更忙了」 | 沒有針對這點的設計目標 | 🟠 已修：CEO KPI |
| 13 | 對話流暢度：requireMention 太僵硬 | 全程要求 @ | 🟡 部分採納（見下） |
| 14 | 用 Response Gating 而非 Mention Gating | — | ⚪ **刻意不採納**（見下） |

🔴 真 bug　🟠 缺口　🟡 部分採納　⚪ 不採納

---

## 一、迴圈保護：我們有一個真的 bug

**他的觀察**：引用研究指出 41.8% 的多 Agent 系統失敗來自**缺少終止條件**；兩個 Agent 互相觀察對方訊息會造成指數級的 token 消耗。

**我們原本的程式**：
```python
m = re.search(r'"hop"\s*:\s*(\d+)', msg.content)
if m and int(m.group(1)) >= CFG.get("max_hops", 6): ...
```
`hop` 從**訊息內容**抓——也就是靠 Agent 自己在 JSON 裡誠實回報並累加。Agent 忘記寫、寫錯、或格式跑掉，`hop` 就重置為 0，**迴圈保護等於不存在**。這是把安全機制建立在「LLM 會照規矩做」之上，違反了我們自己的第一原則（LLM 提案、程式執行）。

**已改**：Router 在 `router_state.db` 開 `chains` 表自己記帳。
- 訊息來自 bot → `hop + 1`
- 訊息來自人類 → 重置為 1
- `hop ≥ 6` → 🛑 中止並要求 CEO 收斂

**另加**：`a2a_turns`（同一 thread 內 Agent 之間的來回輪數），達 5 輪自動升級給 Blacksheep 裁示。這是第二道保險——hop 管的是「鏈有多長」，a2a 管的是「有沒有在原地打轉」。

---

## 二、沉默機制：客套話會無限循環

**他的觀察**：Agent 被訓練得友善，會對「謝謝」「收到」持續回應，形成不終止的交換。OpenClaw 有 `NO_REPLY`，Hermes 沒有。他也指出 **Claude Code Channels 反轉了這個模型——回應需要明確的 tool call，沉默是預設狀態**。

**我們的情況**：我們用 `claude -p`，輸出**一定**會被貼回 Discord。所以我們處在「沉默不是預設」的那一邊，需要顯式機制。

**已改**：
- Router 加 `is_no_reply()`：Agent 回覆以 `NO_REPLY` 開頭且長度 < 200 字 → 只加 💤，不貼訊息，並重置 a2a 計數。
- 憲法第七條：「沉默勝過廢話」。
- PROTOCOL 新增 §5.5，明確列出**該沉默**（客套、討論已收斂、不在職責範圍、結論重複）與**不該沉默**（被指派任務、不同意、失敗了）的情境。

第二組尤其重要——如果只教「可以沉默」，會出現 Agent 用沉默逃避回報失敗。

---

## 三、Discord 的實務細節（會實際爆炸的那些）

**thread 數量**：`#analysis` 每小時一個 1H 掃描 thread × 24 小時 × 多標的 = 一天數十個。原本封存時間寫死 1440 分鐘（24 小時），意味著頻道裡永遠有 40+ 個活著的 thread。
→ 已改成依頻道分層（Discord 只接受 60/1440/4320/10080）：`analysis`、`market-data` 用 60；`tasks`、`backtest`、`meeting-room` 用 4320；`forge` 用 10080。

**thread 命名**：他用 LLM 產 3–6 字標題。我們**不用 LLM**——每小時都在建 thread，用 LLM 命名是持續的額度支出。改成程式從 `[CRON:job]` 的 label、`msg_type`、symbol 產生，例如 `1H掃描 BTCUSDT 09/09 14:05`。45 個排程都補上了中文 label。

**權限靜默失敗**：他因為缺少 Manage Threads 權限 debug 了兩小時，且**沒有任何錯誤日誌**。
→ Router 開機時檢查 16 隻 Bot 的 9 項必要權限，缺任何一項就**拒絕啟動**並列出缺什麼、去哪裡修。這比事後查日誌便宜太多。

---

## 四、對話流暢度：我們部分採納，並說明為什麼

**他的做法**：Response Gating（`allowBots: true` + 在 Agent 設定裡寫規則）而非 Mention Gating（`allowBots: "mentions"`）。他的理由是後者「可靠但不自然」。

**我們的判斷：不採納他的主選項。** 這是價值取捨不同，不是他錯了：

- 他的場景是研究與日常工作，**自然度**優先。
- 我們的場景是會下真錢單的系統，**可稽核性**優先。每一則觸發都要能回答「誰叫它做的」。
- Response Gating 把「要不要回應」交給 LLM 判斷，等於在關鍵路徑上多一個機率性決策。

**但他點出的問題是真的**：全程強制 @ 會讓追問變得很煩——Blacksheep 在 thread 裡問「為什麼是 2.4 而不是 2.6？」還要 @TD-CHART 一次。

**我們的折衷**：**thread 內的隱含收件人**。Router 在建 thread 時記錄主責 Agent；當 Blacksheep 在該 thread 內發言且沒有 @ 任何 Bot 時，訊息自動路由給主責 Agent。
- 只對 **Blacksheep** 生效，Agent 之間仍必須顯式 @（稽核鏈完整）。
- 只在 thread 內生效，頻道層級不變。
- 其他 Agent 不會誤觸（它們不是這個 thread 的主責）。

拿到了自然度，沒有放棄可稽核性。

---

## 五、Harness Engineering：三根支柱對照

他的框架：**評估迴路 + 架構約束 + 記憶治理**。逐項對照：

### 5.1 評估迴路：「你不能讓一個人自己幫自己打分數」

**我們原本的漏洞**：CEO 驗收 FORGE 的交付時，看的是 FORGE **自己在訊息裡貼的** pytest 輸出。那份輸出可能是舊的、是別的檔案的、或根本是編的。這正是他說的反模式。

**已改**：`scripts/verify_delivery.py` — CEO 自己跑，獨立驗證：
- 宣稱的檔案真的存在
- 指定的測試真的通過（自己跑一次）
- `lint_agents.py` 通過
- 上下文完整性通過
- `git status` 真的有變更（防止空交付）

輸出 `{verdict: PASS|FAIL, checks: [...]}`，CEO 直接引用這份結果做 `REVIEW_RESULT`。新的 `change-review` skill 第一步就是「**不要相信交付者貼上來的測試輸出**」。

我們原本就有的評估迴路（值得記下，不是全部都缺）：REDTEAM 盲審、AUDIT 績效稽核、pytest、lint、Router preflight。

### 5.2 架構約束：用強制規則而非指引

他引 OpenAI Codex 的例子：「Types 只能依賴 Types，Service 只能依賴 Types」——用**結構**而非**紀律**維持邊界。

我們原本就相當強：視圖權限（41 個視圖 + 授權矩陣）、工具白名單、切片雜湊、三層分離。

**已補**：`lint_agents.py` 新增依賴方向檢查
- `engine/` 不得 `import agents/`（執行層不該知道思考層存在）
- 任何 Agent 不得被授權 `Write(data/)`（資料倉唯一寫入口是 ingest 服務）
- 根目錄不得有 `CLAUDE.md`（ADR-004）

### 5.3 記憶治理：未驗證的東西不能當知識

**他的原則**：每個經驗初始為未驗證，只有驗證後才升級為可靠知識，避免幻覺在系統中傳播。

**我們原本**：有「禁止自我修改人設」（防止最糟的形式），但 AUDIT 的 `lessons` 與 LAB 的假設是**直接進資料倉、沒有成熟度標記**的。CHART 讀到一條「上次 OB_RETEST 在週五失效」的單次觀察，會把它當事實用。

**已改**：`knowledge` 表 + 三階段

| 階段 | 意思 | 誰能讀 |
|---|---|---|
| `UNVERIFIED` | 單次觀察、推測 | 只有 LAB 與 REDTEAM（他們的工作就是去驗證或推翻） |
| `VALIDATED` | 回測或 ≥ 30 筆樣本驗證過 | CHART、RISK、AUDIT、CEO 可引用 |
| `PROMOTED` | Blacksheep 核准寫進 `shared/` | 是規則，必須遵守 |

隔離做在**視圖層**：`v_knowledge_unverified` 沒有授權給 CHART。它想引用未驗證的線索也拿不到。

---

## 六、Skill 原子性：我們確實有肥大問題

**他的標準**：單一職責、可組合、可獨立測試、可替換、失敗不級聯。反模式是「塞了五件事的詳細流程」。**但他也說「不是所有東西都要原子性」**——目標是有意義的邊界，不是最小單位。

**誠實檢查我們的 31 個 skill**，三個明顯違反：

| 原本 | 混了幾件事 | 拆成 |
|---|---|---|
| `bitget-execution` | 下單 + 掛保護單 + 對帳 + 模式切換 + 合約規格 | `exchange-order-placement`、`exchange-position-guard`、`exchange-reconciliation` |
| `agent-forge` | 重現 + 定位 + 修復 + 審核 + 部署 | `bug-triage`、`fix-and-verify`、`change-review` |
| `growth-analytics` | 抓數據 + 算量尺 + A/B + 週報 | `ig-insights-collection`、`growth-experiments` |

拆分的判準是**「這一段能不能獨立驗收」**。`exchange-position-guard` 的 10 秒止損規則可以單獨測試、單獨替換、單獨歸因失敗；它混在下單流程裡就不行。

其餘 28 個沒有拆——`smc-analysis` 雖然長，但它是一個連貫的分析方法，拆開反而破壞它。這是他說的「不是所有東西都要原子性」。

**每個 skill 現在都有「輸入 / 輸出契約」段落**（輸入什麼、輸出什麼、失敗時怎麼辦）。沒有契約的技能無法獨立測試也無法替換。`lint_agents.py` 現在會檢查：步驟 > 8 個、檔案 > 4000 bytes、缺少契約 → 警告。

**失敗歸因**：`bug_reports` 加 `skill_name`，新增 `v_skill_failures` 視圖。`bug-triage` 的第 5 步要求查這個視圖——同一個 skill 重複出事三次以上，代表是設計問題不是實作問題，要提架構修改而不是繼續打補丁。

### 他的四個生產級標準（已寫進 `01_ARCHITECTURE.md`）
1. **評估精確度**：能指出哪個 skill 失敗與為什麼 → `skill_name` + `v_skill_failures`
2. **圖可讀性**：系統能用紙筆畫在一頁上 → 白皮書的架構圖就是這個測試
3. **錯誤隔離**：失敗侷限在 skill 邊界內 → 契約 + 三層分離
4. **可升級性**：換掉單一 skill 不用重寫系統 → `skills/` 可獨立複製替換

**他引用的數據值得記住**：Terminal Bench 2.0 用**相同模型**但更好的架構提升 14 個百分點；CORE-Bench 從 42% 跳到 95%。這是「harness 比 model 重要」的直接證據——也是為什麼我們把力氣花在切片、權限、驗證這些看起來不性感的地方。

---

## 七、HTML 而非 Markdown：Blacksheep 才是瓶頸

**他的觀察**：收到兩百多行的 Markdown 提案，「不想看」，拖了好幾天。同樣內容做成 HTML（分頁、摺疊、流程圖），**四分鐘看完，留了七個評論**。他的結論：「Markdown 是腦內筆記，HTML 是展示面板。」

**我們的情況**：白皮書已經是 HTML（給 Blacksheep 看的），但**Agent 的日常產出全是 Discord 純文字**——回測報告、止損週報、每日匯報、FIX_PROPOSAL 的 diff。這些正是 Blacksheep 每天要審的東西。一份完整的 `BACKTEST_REPORT`（含 6 段 walk-forward、參數擾動、Monte Carlo）貼進 Discord 是災難。

**已改**：`report-preview` skill + `scripts/render_report.py` 規格 + Dashboard 的 `/reports/<type>/<id>` 路由。
規則：**先產結構化 JSON（真相）→ 渲染 HTML（視圖）→ Discord 只貼一行結論 + 3–5 個關鍵數字 + 連結**。
必須走這條路的輸出：BACKTEST_REPORT、止損週報、月度績效、FIX_PROPOSAL、每日匯報、GROWTH_REPORT、MARKETING_PLAN。

一個細節：**需要 Blacksheep 決定的事必須直接寫在 Discord 訊息裡**，不能只藏在報告連結內——他可能只看訊息不點連結。

---

## 八、「有了 AI 反而更忙了」

**他引述的觀察**：效率提升不會變成閒暇，而是變成管理更大的 Agent 團隊、更複雜的工作流；心智負擔可能超過親手做。

**對我們的意義**：Blacksheep 的期待是「透過 CEO 指揮 15 個 Agent 就會輕鬆」。實際風險是變成**每天讀 15 個 Agent 的輸出**——那比自己交易還累。

**已改**：把它變成 CEO 的**第一 KPI**：
> **Blacksheep 每天花在系統上的時間 ≤ 15 分鐘（正常日）。**

寫進 CEO 的 PERSONA 與 MANUAL：「我的存在就是為了不讓 Blacksheep 被淹沒。我吸收噪音，只把結論、異常、需要他決定的事交給他。」配套的量測是匯報長度（Discord 訊息 ≤ 15 行）。

**他另一個建議我們原本就對了**：「從很小的新專案開始，讓 AI 端到端跑完一次」——這正是 `QUICKSTART.md` 只建 2 隻 Bot 先讓 CEO 活起來的設計。

---

## 九、我們刻意不採納的

| 他的做法 | 我們的選擇 | 理由 |
|---|---|---|
| Response Gating（`allowBots: true` + 行為規則） | 保持 Mention Gating，只對 Blacksheep 開 thread 內隱含收件人 | 交易系統的可稽核性優先於對話自然度；不把「要不要回應」交給 LLM 機率決策 |
| LLM 產生 thread 標題 | 程式產生 | 每小時都在建 thread，用 LLM 命名是持續的額度支出，而我們的訊息有結構（cron label / msg_type / symbol）足以命名 |
| 把所有 skill 都拆到原子 | 只拆了 3 個 | 他自己也說「不是所有東西都要原子性」；`smc-analysis` 拆開反而破壞方法的連貫性 |
| Vercel 部署提案頁 | 本機 Dashboard 的 `/reports/` 路由 | 報告含交易資料，不上公網 |

---

## 十、還沒做、但記在這裡的

1. **Discord 評論功能**：他的 `/preview` 有 Google Docs 式的行內評論。我們的 `/reports/` 目前只能看不能評。第二階段可以加（存進 `knowledge` 表當 UNVERIFIED 線索）。
2. **`NO_REPLY` 的濫用監控**：如果某個 Agent 的 `NO_REPLY` 比例異常高，可能是它在逃避工作。WATCH 應該把它加進健康指標。
3. **跨模型紅隊**：他沒提，但我們自己的限制仍在——REDTEAM 目前只能用「盲審 + opus + 對抗式立場」替代真正的跨模型審核。有第二個模型來源時這是第一個該補的。

---

## 參考來源
- [Harness Engineering 與 Skill Atomicity](https://hanamizuki.tw/the-case-for-harness-engineering-and-skill-atomicity/)
- [多 Agent 對話的 Harness 技巧](https://hanamizuki.tw/openclaw-hermes-agent-to-agent-conversation/)
- [讓 Agent 對話更流暢（Discord workflow）](https://hanamizuki.tw/openclaw-discord-workflow/)
- [為什麼我請 AI 把每份提案都做成 HTML](https://hanamizuki.tw/html-preview-instead-of-markdown/)
- [如何在團隊導入 AI（AppWorks AI Founder Day 2026）](https://hanamizuki.tw/appworks-ai-founder-day-2026/)
