# 變更紀錄（CHANGELOG）

> 白皮書正文只描述**系統現況**；這裡記錄每一版改了什麼、為什麼改。
> 想知道「這個機制為什麼存在」時看這裡——很多機制的來由是一次真實的失誤。

## 各版變更

**v3.0.18**（存檔失敗卻說「沒東西可存」）：
183. **`snapshot.cmd` 用 `git commit && echo Saved || echo Nothing to save` 判斷結果。**
     git 因為沒設 `user.email` 而失敗時，使用者看到的是 **Nothing to save**——
     以為工作區乾淨，其實是**根本沒存到**。這跟 v3.0.10 那批「錯誤被吞掉」是同一類錯誤，
     只是換到批次檔裡。現在分三種情況各自回報：不是版本庫、沒有變更、commit 失敗
     （並直接把 `Author identity unknown` 的解法印出來）。測試 126 → **127 項**。

**v3.0.17**（.cmd 的編碼：cp950 主控台把批次檔吃掉）：
180. **`.\snapshot.cmd` 一執行就噴 `'賣' 不是內部或外部命令`。**
     cmd.exe 以**主控台的 ANSI codepage**（繁中 Windows 是 cp950）讀批次檔，
     而檔案是 UTF-8。中文註解的位元組被當成 cp950 的雙位元組字元，吃掉後面的 ASCII——
     連 `if "%MSG%"==""` 都裂成 `G"=="" set MSG=checkpoint`。
     `.cmd` / `.bat` 一律改成**純 ASCII + CRLF**，說明文字搬到 `dev/CLAUDE.md`。
181. **同一個病因也在 `.ps1` 上。** `router/start.ps1`、`router/watchdog.ps1` 都是
     無 BOM 的 UTF-8；PowerShell 5.1（Windows 內建那版）沒有 BOM 就以 ANSI 讀。
     兩支都補上 UTF-8 BOM 與 CRLF。
182. 兩條新測試把規則釘住：`.cmd`/`.bat` 必須純 ASCII 且 CRLF；含非 ASCII 的 `.ps1`
     必須有 BOM。`.gitattributes` 補上 `*.ps1 text eol=crlf`。測試 124 → **126 項**。

**v3.0.16**（Windows 上真的能用的 git 設定）：
178. **新增 `.gitattributes`。** Windows 的 CRLF 會讓 diff 變成「整個檔案都改了」——
     而看得懂 diff 正是用 git 的全部意義。一律以 LF 入庫；`.cmd` / `.bat` 例外用 CRLF；
     `.sh` 強制 LF（CRLF 的鉤子在 Git Bash 會 `bad interpreter`）。
179. **新增 `dev/snapshot.cmd`**：動手之前先存一個 checkpoint commit（`--no-verify`，
     因為它只是存檔點不是要推出去的東西）。搭配 `dev/CLAUDE.md` 新增的分支指引。
     測試 122 → **124 項**。

**v3.0.15**（git 閘門實跑：DAY0 的第一個 commit 會被自己擋下來）：
174. **金鑰掃描器會抓到自己的測試假金鑰。** `tests/` 裡有兩個「長得完全像真的」的
     假 token——那正是測試掃描器有沒有效的方式。結果 DAY0 步驟 3B 的
     **第一個 commit 就被自己的 pre-commit 擋下**。新增逐行豁免
     `# check_secrets: allow`（只豁免那一行，同檔案其他行照抓），並加測試確認豁免夠窄。
175. **`--all` 掃到 `__pycache__` 裡的 .pyc**，還真的在編譯結果裡找到那個假金鑰。
     目錄排除原本只看第一層，改成任一層命中即跳過，並略過二進位副檔名。
176. **git 鉤子寫死 `python`。** 鉤子由 git 執行，**venv 不會是啟動狀態**——
     系統那支 python 可能沒有相依套件甚至不存在，鉤子會以「找不到模組」失敗，
     看起來像專案壞了。三個鉤子改成先解析 `.venv/Scripts/python.exe`（Windows）或
     `.venv/bin/python`。`pre-push` 另外補上 `build_context.py --verify`，
     並把 `pytest -q` 限定成 `pytest tests -q`（否則會掃到 `legacy/` 與 `.venv/`）。
177. 整條流程在乾淨副本上實跑驗證：`git init` → 裝鉤子 → 第一個 commit 成功；
     再故意植入一把假 token，pre-commit 確實擋下、commit 數維持 1。測試 121 → **122 項**。

**v3.0.14**（開發 session 的啟動方式：ADR-004 遇上工作目錄邊界）：
171. **`dev/CLAUDE.md` 教的做法在 Claude Code 上其實開不起來。** ADR-004 要求
     開發 session 從 `dev/` 啟動（根目錄不得有 CLAUDE.md，否則 15 個 Agent 全部會載入它）。
     但 Claude Code 的檔案存取以**啟動目錄**為界——從 `dev/` 啟動的 session
     預設讀不到 `../engine/`、`../scripts/`、`../tests/`，而那正是要改的東西。
     新增 `dev/dev.cmd`：`claude --add-dir ..`，並在 `dev/CLAUDE.md` 寫清楚為什麼不能省。
172. **新增 `/td-check` 斜線指令**（`dev/.claude/commands/td-check.md`）：
     一次跑完六支驗證程式。這條鏈就是「開發 session 不會違反白皮書」的保證來源——
     不是靠記性。斜線指令只有被呼叫才載入，不會污染 Agent 的繼承鏈。
173. 三條新測試：啟動器必須有 `--add-dir ..`；`/td-check` 必須涵蓋六支驗證；
     `CLAUDE.md` 只能出現在 `dev/` 與 `agents/`。測試 118 → **121 項**。

**v3.0.13**（Agent 互丟中止訊息：9719 跳的無限迴圈）：
165. **災難的正主：`msg.reply()` 預設會 @ 被回覆訊息的作者。**
     Discord 的 reply 預設 `mention_author=True`，被回覆者會被放進 `msg.mentions`。
     而 Router 判斷「我有沒有被叫到」用的是 `bot.user in msg.mentions`——
     於是「某個 Bot 回覆了我」就等於「我被 @ 了」：

         RISK 撞上限 → 回覆（自動 @CEO）→ CEO 被觸發 → CEO 也撞上限
         → 回覆（自動 @RISK）→ RISK 被觸發 → ……

     兩隻 Bot 以機器速度互丟「鏈中止」訊息。實測跳到 **9719**。
     兩邊都補：上限通知改走 `human_reply()`（`replied_user=False`），
     而「被叫到」的判斷改成**內容裡真的寫了 `<@id>`**——被回覆不算被叫到。
166. **排程訊息被算成「Agent 又傳了一跳」。** 排程由 TD-ROUTER（一隻 Bot）發出，
     而跳數只有人類發言才歸零。所以那個頻道每跑一次排程就 +1，第 7 次之後
     **每一次排程都只回「傳遞已達 N 跳上限」**，N 一路往上爬。
     現在 cron 觸發等同新任務（`from_bot=msg.author.bot and not cron_job`），
     並新增 `chain_idle_reset_minutes: 30`——一條鏈閒置夠久就算結束。
167. **中止訊息原本 @ TD-CEO。** 但這條鏈已經滿了，CEO 一進來也立刻撞同一個上限，
     所以「TD-CEO 都不處理」不是 CEO 壞了，是設計把它放在一個做不了事的位置。
     現在改 @ Blacksheep，而且**同一條鏈只喊一次**（`chains.alerted`）。
168. **新增不講道理的最後一道閘：同一頻道 60 秒內處理超過 20 則就靜音 10 分鐘。**
     跳數與輪數是「講道理」的保護，總會有沒想到的路徑繞過去；這道閘不看原因只看速率。
169. **測試會污染 Router 的正式狀態庫。** `router_state.db` 路徑現在可用 `TD_STATE_DB`
     覆寫，測試一律指向暫時檔案——不然跑一次 pytest 就讓真實頻道被算了好幾跳。
170. **lint 第 33 項**：`.reply()` 不得不關掉 `replied_user`；不得用
     `bot.user in msg.mentions` 判斷有沒有被叫到。lint 32 → **33 項**，測試 110 → **118 項**。

**v3.0.12**（測試撞到真實狀態：outbox 殘留）：
162. **`test_handle_no_reply_path` 在 Blacksheep 的機器上失敗、在乾淨 checkout 上通過。**
     測試沒有換掉 `agent_dir()`，於是讀到**真實的** `agents/chart/outbox/`——
     他那台有上一次跑剩的檔案，`is_no_reply(text) and not files` 因此為假，
     走了正常回覆路徑（✅ 而不是 💤）。測試不該依賴工作目錄的殘留狀態：
     `_prepare()` 現在把 `agent_dir` 指到一個暫時目錄，並可用 `outbox_files=` 明確造殘留。
163. **順帶抓到一個真的 bug：outbox 有檔案時，「NO_REPLY」四個字會被貼到 Discord。**
     原本是 `if is_no_reply(text) and not files:` —— 條件不成立就直接
     `send_long(ch, text, files)`，而那個 `text` 就是字串 "NO_REPLY"。
     現在拆成兩層：沒檔案才走 💤；有檔案則照送檔案，但換成一句人看得懂的說明，
     並記一筆 warning（殘留通常代表上一次寫完檔案就崩潰或斷線）。
164. **preflight 會在啟動時列出所有 outbox 殘留。** 殘留檔案會跟著下一次發言送出，
     而且是送在不相干的對話裡——這種事要在啟動時看得見，不是事後才發現。
     測試 109 → **110 項**。

**v3.0.11**（第一次真的跑進 handle()：兩個「一觸發就死」的 bug）：
158. **`AttributeError: 'Message' object has no attribute '_agent'`——每一次觸發都失敗。**
     `handle()` 的開頭是 `msg._agent = aid`，想把 agent id 掛在訊息上讓 `react()` 之後讀回來。
     但 `discord.Message` 有 `__slots__`、沒有 `__dict__`，**掛屬性會直接 AttributeError**。
     這行在函式的第一行，所以 RISK / WATCH / EXEC 只要被排程叫到就立刻失敗，
     Discord 上看到的是「TD-RISK 這次處理失敗」——看起來像 Agent 的問題，其實是 Router 的第一行。
     改法：`react(msg, emoji, remove=..., aid=aid)` 用**參數**收 agent id，
     八個呼叫點全部改過；不再往任何別人的物件上掛狀態。
159. **錯誤處理器自己丟出新的錯誤。** `handle()` 的 `except` 區塊要 @FORGE 開 BUG_REPORT，
     寫的是 `CFG["agents"]["forge"]["mention"]`——但 `mention` 是 `on_ready` 才寫進去的。
     FORGE 的 Bot 還沒上線時就是 `KeyError: 'mention'`，**原始錯誤被覆蓋**，
     人看到的訊息與真正的病因無關。現在有 `mention_of(aid)`（Bot 沒上線就回退成純文字），
     整段送出再包一層 try/except：錯誤處理器不可以有失敗路徑。
160. **這兩個 bug 是被新測試找出來的，不是被使用者找出來的（第二個是）。**
     `tests/test_router_handle.py` 用假的 Discord 物件**實跑** `handle()` 五條路徑
     （LLM 正常、NO_REPLY、失敗回報、表情、不得掛屬性）。假的 `Message` **故意加上
     `__slots__`**，讓「往別人的物件掛屬性」這種寫法死在 CI，而不是死在實盤的排程上。
     每個假頻道發一個唯一 id——共用 id 會讓上一個測試留下的鏈跳數累加到下一個測試，
     單獨跑會過、整份跑會掛，這種假失敗比真 bug 還難查。
161. **lint 第 31、32 項**（共 32 項）把這兩個模式變成靜態檢查：
     不得往 `msg.*` / `message.*` 指派屬性；`mention` 一律走 `mention_of()`。
     兩項都有「植入違規 → lint 必須抓到」的回歸測試。測試 101 → **109 項**。

**v3.0.10**（Router 跑起來之後：四個「錯誤被吞掉」的 bug）：
152. **45 個排程全部靜默失效。** `setup_scheduler` 包了一層
     `lambda j=job: asyncio.ensure_future(fire(j))`。那個 lambda 是**同步函式**，
     AsyncIOExecutor 看到同步函式會丟進執行緒池，而執行緒裡沒有事件迴圈：

         RuntimeError: There is no current event loop in thread 'asyncio_13'
         RuntimeWarning: coroutine 'fire' was never awaited

     `fire` 本來就是 coroutine，直接 `sch.add_job(fire, ..., args=[job])` 即可，
     AsyncIOExecutor 會在迴圈上 await。順便讓啟動日誌印出最近三個排程的實際觸發時間。
153. **`@TD-CEO !status` 完全沒反應，而且日誌乾乾淨淨。** `worker()` 寫的是
     `try: await handle(...) finally: q.task_done()`——**沒有 except**。
     `handle()` 只要丟一次例外，那個 while 迴圈就結束、worker 任務永久消失，
     asyncio 的未處理例外通常也不會印出來。**該 Agent 從此不回應任何訊息。**
     現在：記完整堆疊、在 Discord 回一句人看得懂的話、迴圈繼續活著；
     worker 若真的結束了，`add_done_callback` 會大聲說「該 Agent 從現在起不會回應」。
154. **`[-800]` 取的是一個字元，不是最後 800 字。** `run_claude` 與 `run_script` 的
     錯誤訊息都被毀成單一字元。改成 `[-800:]`，並在 stderr 為空時改端 stdout。
155. **日誌 17:03、排程卻說 01:03+08:00，差整整八小時。** 排程本身是對的
     （它直接用 `scheduler.yaml` 的 `Asia/Taipei`），錯的是日誌時間戳跟著作業系統跑。
     Windows 的 C 執行庫不認得 `Asia/Taipei` 這種 IANA 名稱，`router/.env` 的
     `TZ=Asia/Taipei` 會被忽略或讓本機時間退回 UTC。
     **08:00 台北是這個系統的日界線**，時間戳誤導在交易系統裡是危險的——
     改成 `_TzFormatter` 一律用交易時區，`CronTrigger` 也明確綁 `timezone=TZ`，
     並在 preflight 印出「交易時區現在幾點 / 作業系統時區是什麼」讓落差看得見。
156. **lint 第 30 項**把這三個模式變成永久檢查（worker 必須有 except、
     不得有單字元切片、不得用 `asyncio.ensure_future`——用 AST 判斷，註解裡提到不算）。
157. 測試 96 → **101 項**，其中一項是**實跑**：讓 handle 故意丟例外，
     確認後面兩則訊息仍被處理。

**v3.0.9**（子程序的編碼：cp950 的第二回合）：
146. **`python router\discord_router.py` 噴出四組 `UnicodeDecodeError: 'cp950' codec can't decode`。**
     `preflight()` 用 `subprocess.run(..., text=True)` 但沒指定 `encoding`，
     Python 就用系統地區編碼（Windows 繁中 = cp950）去解我們 UTF-8 的中文輸出。
     **最陰險的是主程式看起來還是成功的**——例外發生在 subprocess 的讀取執行緒，
     主程式拿到空字串、returncode 仍是 0，於是照樣印「preflight OK」。
     真正失敗時你會拿到一個空的錯誤訊息，跟 v3.0.5 那個 `ERROR [19]` 一模一樣。
147. **v3.0.5 只修了 lint 那一支，這次一次修完 13 處**（router 3、check_secrets 6、
     doctor 2、backup_mirror / guard_paths / verify_delivery / verify_docs_claims 各 1，
     外加測試檔 5 處）。新增 `scripts/td_proc.py` 當唯一入口：
     強制 `encoding="utf-8", errors="replace"`，並把子程序環境設成
     `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`，兩端都不會再撞編碼。
148. **lint 第 29 項**用 AST 掃出「以文字模式呼叫子程序卻沒給 encoding」的每一處。
     寫這條檢查時它立刻抓到測試檔裡還有 5 個漏網——這正是它存在的理由。
149. Router 的 `preflight()` 失敗時改為 **stdout 空就端 stderr**，
     跟 lint 的 `run_check()` 對齊：任何子程序崩潰都不可能再產生空的錯誤訊息。
150. 順帶修掉 lint 第 27 項會被自己的註解觸發（第 29 項的註解裡提到了那個函式名）。
     判斷前先濾掉註解行。
151. 測試 93 → **96 項**（新增：全專案不得有沒給 encoding 的文字模式子程序呼叫、
     Router preflight 必須走 td_proc 且失敗時看 stderr、td_proc 實跑取回中文輸出）。

**v3.0.8**（Discord 後台改版：兩個步驟做不下去）：
141. **關不掉 Public Bot。** 錯誤訊息是「私人應用程式不得使用預設授權連結。請確認安裝分頁中的
     預設授權連結設定為『無』」。Discord 不允許私人應用程式同時保有官方產生的安裝連結，
     所以**順序是反的**：先 **Installation → Install Link → None** 存檔，才關得掉 Public Bot。
     手冊原本把這一步整個漏掉。三份文件（`02_SETUP_GUIDE`、`DAY0_RUNBOOK` 步驟 6、
     `QUICKSTART`）都補上，並把使用者會看到的錯誤訊息原文寫進失敗排除表。
142. **第二層原因**：若 Install Link 連 None 都存不了，是這個應用程式開了 App Discovery
     （discoverable 的應用程式必須有安裝參數或自訂網址）。要先到 **App Discovery → Disable Discovery**。
     一般新建的應用程式不會遇到，但遇到時完全查不到原因，所以寫進表裡。
143. **OAuth2 的 Scopes 清單有二十幾項**（identify、email、guilds、rpc.*、applications.* …），
     手冊只寫「Scopes：✅ bot」讓人以為自己找錯頁面。改成明講那是 Discord 的完整清單、
     **只勾 `bot` 一個**，並說明為什麼連 `applications.commands` 都不需要——
     本專案不用斜線指令，Owner 指令走 `!approve` 文字訊息，Agent 靠 @mention 觸發。
144. DAY0 步驟 6 由六個動作改為**七個**，並補上四列的失敗排除表
     （含最常見的「忘記開 MESSAGE CONTENT INTENT → Bot 上線但完全不回應」）。
145. 測試 91 → **93 項**（新增：三份文件都必須教 Install Link 設 None 且順序在關 Public Bot 之前、
     必須寫明只勾 bot scope）。

**v3.0.7**（多專案盤點的指令是舊的）：
136. **`docs/08_BUILD_PLAN.md` 教人打 `scan_legacy.py --src X --out Y --json Z`——`--out` 與 `--json` 根本不存在。**
     那是單專案時代的舊寫法，`scan_legacy.py` 早就改成登錄表模式（`--all` / `--project` / `--src`），
     照著打只會拿到 argparse 的 `unrecognized arguments`。
     已改成正確的三步：`Copy-Item projects.yaml.example` → 填登錄表 → `--all`。
137. **新增 lint 第 28 項**：文件裡教使用者打的每個 `--參數`，
     用 AST 讀出那支腳本 argparse 實際收的旗標來比對。實測會抓到上面那兩個。
     這類「文件教的指令根本跑不動」是最傷人的錯——使用者會以為是自己打錯。
138. 同一段還修掉兩個殘留：`pip install -r router\requirements.txt`（路徑錯，v3.0.4 已在
     DAY0 修過但 BUILD_PLAN 漏了）、以及在裝金鑰閘門之前就 `git add .` 的危險順序。
139. `verify_docs_claims` 不再檢查 CHANGELOG 引用的檔案路徑——它會引用第三方套件的檔案
     當證據（例如 `pandas/io/clipboard/__init__.py` 是 v3.0.6 那個 bug 的現場）。
140. 測試 89 → **91 項**（新增：文件不得教不存在的參數、舊專案盤點必須是多專案流程）。

**v3.0.6**（掃全樹的檢查掃到了 .venv）：
132. **`ERROR [24]` × 163 筆，全部在 `.venv\Lib\site-packages\` 底下。**
     lint 第 24 項用 `ROOT.rglob("*.py")` 比對 requirements.txt，
     於是開始檢查 pandas、pip 自己的原始碼——`import AppKit`、`import ConfigParser`
     當然不在我們的 requirements 裡。我的環境沒有 `.venv` 所以一路是綠的，
     **使用者一建好虛擬環境就爆炸**。
     修法：`scripts/td_paths.py`（新）把「哪些檔案算是這個專案自己的」變成單一定義
     （排除 `.venv`/`venv`/`site-packages`/`__pycache__`/`node_modules`/`build`/
     `worktree`/`legacy`/`data`/`logs`），lint 第 24 項與兩項測試改用它。
133. **lint 第 26 項誤判 `td_paths.py`**：它只有 docstring 是中文、根本不 print 東西。
     判準改成用 AST 找「真的會 `print` 非 ASCII」的呼叫，而不是看整份檔案有沒有中文。
134. **回歸測試直接複製整個專案並造一個假的 `.venv`**（含 `pandas/io/clipboard/__init__.py`
     的 `import AppKit` 與 `pip/_vendor/distlib/compat.py` 的 `import ConfigParser`），
     再實跑 lint，確認輸出裡不出現 `AppKit` 或 `site-packages` 且回傳 0。
     這個坑以後只會在 CI 裡再現，不會在使用者那裡。
135. 測試 87 → **89 項**。

**v3.0.5**（Windows 主控台編碼 + 模組邊界）：
129. **`ERROR [19] 隔離驗證失敗：` 後面一片空白。** 根因是 Windows 的 cp950 主控台：
     `verify_isolation.py` 印 `⚠️` 時丟 `UnicodeEncodeError` 直接崩潰，
     stdout 因此是空的、訊息全在 stderr——而 lint 只挑 stdout 裡開頭是 ERROR 的行。
     **兩邊都修**：
     - `scripts/td_console.py`（新）：把自己這個行程的 stdout/stderr 轉成 UTF-8，
       17 支會印中文的腳本都掛上，**lint 第 26 項**強制。
     - `lint_agents.run_check()`（新）：子程序環境帶 `PYTHONIOENCODING=utf-8`、
       這一端以 UTF-8 解碼，而且**沒有 ERROR 行時就端出 stderr 的最後幾行**。
       **lint 第 27 項**禁止 `main()` 再直接呼叫子程序。已用「故意讓它崩潰」實測過。
130. **跑 lint 卻冒出「已產生 ... TRADE-DESK_whitepaper.html（581 KB，17 個分頁）」。**
     `build_site.py` 是頂層腳本，lint 第 22 項 `from build_site import orphan_table_rows`
     等於**每次 lint 都把整個站台重建一次**（慢、會寫檔，在 Agent 沙箱下還會踩到 denyWrite）。
     表格檢查抽成 `scripts/md_tables.py`；`build_site.py` 加上「被 import 就丟 ImportError
     並告訴你該 import 誰」的防呆。
131. 測試 83 → **87 項**（新增：非 ASCII 腳本都掛 td_console、cp950 下實跑 verify_isolation、
     import build_site 不會建站台、lint 不得回報空錯誤）。

**v3.0.4**（Windows 部署實戰：venv 與路徑）：
122. **`DAY0_RUNBOOK` 步驟 3 叫使用者 `pip install -r router\requirements.txt`——那個檔在專案根目錄。**
     照著做一定失敗。已改為 `python -m pip install -r requirements.txt`，並新增 **lint 第 25 項**：
     文件裡 `-r`、`notepad`、`Copy-Item` 用到的**反斜線路徑**也要存在
     （原本的檢查只認 `python scripts/x.py` 這種正斜線形式，所以漏掉了）。
123. **改用 `python -m pip` 而非 `pip`**：`pip.exe` 是啟動器，裡面**寫死了建立當下的 python 絕對路徑**。
     `.venv` 一旦被搬走、改名，或上層資料夾改過名字，就會噴
     `Fatal error in launcher: Unable to create process using ...`。
     `python -m pip` 不看那串路徑。步驟 3 附上「砍掉重建 venv」的整塊指令。
124. **`doctor.py` 新增【1B】專案路徑與虛擬環境**：
     路徑含空格、位於 OneDrive / 桌面 / 文件 等會被雲端同步的資料夾、含非 ASCII 字元；
     `pyvenv.cfg` 記錄的 python 還在不在；`pip.exe` 裡寫死的路徑是否指回這個 venv；
     目前的 python 是不是就是 `.venv`。三種情況都實測過會被抓到。
125. **步驟 3 補上「放在哪裡」的硬性要求**：不能有空格、不要放桌面或文件（OneDrive 會鎖檔，
     45 個排程 + SQLite **資料庫損毀是真的會發生**）、不要放在中文資料夾下。
126. 步驟 3 原本重複做了一次 `git init / add / commit`（還寫著 v2.7），
     與步驟 3B 衝突且**順序危險**——在裝金鑰閘門之前就 commit。已移除，版本控制統一在 3B。
127. **`verify_docs_claims` 不再改寫 CHANGELOG 的數字**。CHANGELOG 的工作就是記錄
     「當初那個數字錯了」，`--fix` 把歷史改成現況等於湮滅證據。
128. 測試 80 → **83 項**。

**v3.0.3**（進度核對時抓到的兩個漏網）：
120. **`legacy/projects.yaml.example` 被 `.gitignore` 連坐擋掉。** `.gitignore` 寫的是 `legacy/`，
     於是範本檔不會進版控——從 GitHub clone 下來之後，`DAY0_RUNBOOK` 步驟 4 的
     `Copy-Item legacy\projects.yaml.example legacy\projects.yaml` 會找不到來源。
     改成 `legacy/*` + `!legacy/projects.yaml.example`，並實測「範本被追蹤、實際清單仍被忽略」。
121. **測試數也會漂**：`docs/13_GITHUB.md` 停在 69 而實際 80。
     `verify_docs_claims` 加上 `tests` 這個事實，且**用 `pytest --collect-only` 自己數**——
     數 `def test_` 會漏掉 parametrize 展開的那 7 個。

**v3.0.2**（可執行性稽核：把「照手冊做會卡住」的地方全部找出來）：
111. **`requirements.txt` 漏了三個套件**：`APScheduler`、`python-dotenv`、`Markdown`。
     照手冊 `pip install -r requirements.txt` 之後，Router 在**步驟 8 啟動時**才會
     `ModuleNotFoundError`——最晚、最難查的時間點。新增 **lint 第 24 項**：
     用 AST 掃出全部第三方 import，逐一比對 requirements.txt。
112. **`.env` 少填一個鍵會得到裸的 `KeyError: 'OWNER_USER_ID'` + traceback**。
     改為 `require_env()`：先確認 `router/.env` 存在，再檢查三個啟動必填值
     （`OWNER_USER_ID` / `GUILD_ID` / `DISCORD_TOKEN_ROUTER`），並直接告訴你去哪裡拿。
113. **Day 0 只建 2 隻 Bot 時 Router 會炸**：`os.environ[a["token_env"]]` 對還沒建的 Bot
     直接 KeyError。改成跳過並在啟動日誌列出「尚未啟動哪幾隻、去哪裡補」——
     這本來就是 Day 0 的正常狀態（步驟 6 建 2 隻、步驟 11 才建其餘 14 隻）。
114. **`scripts/doctor.py`**：開工前健檢。工具版本與 Python 套件、`claude --version`、
     **`claude -p` 冒煙測試（含逾時後的三種常見原因診斷）**、五個驗證器、
     `.env` 的啟動必填值與已填 token 數、目前的隔離層級。回傳 0 / 1 / 2。
     已接進 CI 與 `DAY0_RUNBOOK` 步驟 8。
115. **`DAY0_RUNBOOK` 新增步驟 2B**：專門處理「`claude -p` 沒反應」。
     關鍵事實：`--output-format json` **不會邊跑邊印**，跑完前畫面全白，很像當掉；
     而 `claude -p` 不帶提示詞時會**讀 stdin**，沒給就永遠等下去。
     另附未登入、PATH 未生效、PowerShell 執行原則、中文亂碼的對照表。
116. **排程指向不存在也沒排進 BUILD_PLAN 的程式**：`refresh_universe.py`（FEED 的宇宙重算）
     與 `engine/marketing_metrics.py` 兩個靜默缺口——排程會觸發，但永遠沒有東西可跑。
     已補進 BUILD_PLAN，並新增 **lint 第 23 項**永久防堵。
117. **`verify_docs_claims` 把 `names[0]` 這種陣列索引算成第 0 項 lint 檢查**，
     導致文件宣稱的檢查數多一。改成只認問題訊息開頭的 `[N]`。
118. 白皮書引用 `docs/adr/ADR-004` 少了副檔名；schema 以記憶體 SQLite 實跑確認
     32 表 / 44 視圖建得起來、且沒有任何視圖是沒人被授權的。
119. 測試 72 → **80 項**（新增：全部 .py 可編譯、排程程式存在或已排進 BUILD_PLAN、
     文件不叫使用者跑不存在的程式、doctor 可在乾淨環境跑完、Day 0 手冊有記載
     `claude -p` 的冒煙測試、Router 缺 .env 時給可行動訊息、Router 跳過未建的 Bot、
     requirements 涵蓋全部 import）。

**v3.0.1**（修正 v3.0 的兩個回歸 + 改以 Windows 原生為預設）：
104. **修正：白皮書 §2.3b 的表格被我插壞。** v3.0 把「權限隔離（OS 層）」那一列插在表格之外，
     Markdown 會把它印成裸的 `|` 字元——這就是「白皮書架構沒延續」的直接原因。已移回表格內。
     並新增 **lint 第 22 項**與兩項測試：掃描 `docs/*.md`、`shared/*.md` 的孤兒表格列，
     偵測器本身也有測試（含「程式碼區塊裡的管線字元不算」）。
105. **修正：HTML 站台弄丟了 v2.9 的 15 分頁架構。根因是產生器只住在暫存區。**
     v2.9 那支產生器（住在暫存區的 build\_html\_v29）從來沒進版控，換一次 session 就消失，
     所以 v3.0 交付時只能臨時重寫，把 15 個分頁壓成 1 頁。
     已把它連同 `docs/site.css` 與 `docs/agents_meta.json` 一起搬進 repo：
     **`scripts/build_site.py`**，17 個分頁（v2.9 的 15 個 + 「邊界」+ 「GitHub」）——
     總覽（含 KPI 與四層知識模型 SVG）／白皮書／架構／建置流程／邊界／GitHub／Harness／
     開發環境／Agent（15 張卡，PERSONA + MANUAL 可展開）／Skills（39 個）／規格（shared 全文）／
     Router（可執行程式全文）／教學／維運／路線圖／ADR／術語。
     三項測試釘住：v2.9 的每個分頁都還在、15 個 Agent 與 39 個 Skill 都在站台裡、
     **產生器不得依賴暫存區路徑**（`"/tmp/" not in src`）。
105b. **同時抓到 2 個真的沒渲染出來的表格**：Markdown 的表頭若緊接在段落之後，
     會被吸進那個段落，印出裸的 `|` 字元——`docs/09_HARNESS_LESSONS.md`
     與 `shared/CONSTITUTION.md` 各有一處，已修。偵測規則併進 lint 第 22 項，
     另有一項測試**實際渲染一次**，確認 84 個表格全部變成 `<table>`。
106. **改以原生 Windows 為預設執行環境**（Blacksheep 的實際環境）。
     新增 `TD_REQUIRE_SANDBOX`（`router/.env`，預設 `0`）：
     `0` = 原生 Windows，不要求 OS 沙箱，隔離 = L1 + L2 + L3；
     `1` = macOS / Linux / WSL2，要求沙箱，沙箱起不來的呼叫直接失敗。
     v3.0 原本硬寫 `failIfUnavailable: true`，在 Windows 上會讓**每一次 Agent 呼叫都失敗**。
107. **Router `preflight()` 大聲宣告隔離層級**：L0 未啟用時印出警告並說明目前有哪幾層、
     代表什麼（「抓得到並自動還原，不是擋得住」）。最糟的失效模式是「以為有沙箱」。
108. **`verify_isolation.py` 的逃逸報告改為執行期判斷**：依平台與 `TD_REQUIRE_SANDBOX`
     分別印出「已由 L0 封住」／「規則已備妥但目前未生效」／「連規則都沒有」。
     設定檔寫了不等於生效，報告不該假裝。
109. `DAY0_RUNBOOK.md` 步驟 0 改寫為「確認隔離層級（Windows 原生）」，
     WSL2 降為可選升級並說明它是 Windows 內建功能、不是換作業系統；
     `docs/13_GITHUB.md` 第五節的指令全部改為 PowerShell，並補上
     「原生 Windows 上 `~/.ssh` 沒有沙箱保護」的誠實註記。
110. 測試 64 → **69 項**。

**v3.0**（數位邊界補上 OS 層 + GitHub 治理）：
95. **L0 作業系統層沙箱**：`scripts/sync_sandbox.py` 由 `OWNERSHIP.yaml` 生成 15 份 `sandbox` 設定
    （`filesystem.allowWrite/denyWrite/denyRead`、`network.allowedDomains`、`credentials.files/envVars`），
    lint 第 21 項驗證同步。Claude Code 的沙箱用 bubblewrap（Linux/WSL2）/ Seatbelt（macOS），
    限制**套用到 Bash 指令與其所有子程序**——FORGE 與 LAB 的逃逸路徑至此真正封住。
96. **`denyRead` 鏡射工具層**：工具層每一條 `Read(...)` deny 自動翻成沙箱 `denyRead`。
    在此之前 CHART 被 deny `Read(shared/RISK_RULES.md)` 卻能用 Bash `cat` 讀到——Goodhart 防護是紙做的。
    兩個刻意例外：`data/`（授權查詢路徑 `query_readonly.py` 是 Bash 子程序，必須開得了 db）、
    自己的身分檔（沙箱比對真實路徑，不排除會把 Agent 鎖在門外）。
97. **Router 帶上 session 硬化**：`strictAllowlist` / `allowUnsandboxedCommands:false` / `failIfUnavailable:true`
    只有 CLI `--settings` 或使用者設定能開（專案設定會被忽略），所以由 Router 每次呼叫時帶上。
    `failIfUnavailable` 讓沙箱起不來時**啟動即失敗**，而不是靜默降級成沒有保護。
98. **發現：原生 Windows 沒有沙箱**。`DAY0_RUNBOOK.md` 新增**步驟 0**（選 WSL2 還是原生 Windows，
    含 bubblewrap/socat 安裝與 Ubuntu 24.04 的 AppArmor user-namespace 修正）。
    這是整個 v3.0 最重要的一項：沒有 WSL2，L0 完全不存在。
99. **GitHub 治理**：`.github/workflows/ci.yml`（金鑰掃描 → 生切片 → lint 21 → 隔離 → 文件宣稱 → pytest，
    另有每週一 09:00 台北的定期驗證抓環境腐化）、`.github/PULL_REQUEST_TEMPLATE.md`、`requirements.txt`。
100. **自製 push protection**：查證後確認 GitHub Free 方案的**私有庫沒有 secret scanning，也沒有分支保護**，
    伺服器端擋不住任何東西。因此 `scripts/check_secrets.py`（10 類金鑰樣式 + `--history` 全歷史掃描）
    與 `scripts/install_git_hooks.py`（pre-commit / pre-push / post-commit）把防線放回本機。
101. **3-2-1 備份**：`scripts/backup_mirror.py`（`git bundle --all` + 鏡像 clone + `.env` 鍵名清單）。
    GitHub 是遠端副本不是備份——帳號停權、誤刪、force-push 都會讓它跟著消失。
102. **新文件**：`docs/12_DIGITAL_BOUNDARY.md`（四層邊界 + 外部實務對照 + 已知缺口 thread-history 旁路）、
    `docs/13_GITHUB.md`（要不要用／用哪三件事／Free 方案少了什麼／不建議做的事）。
    `DAY0_RUNBOOK.md` 新增**步驟 3B**（git init → 金鑰掃描 → 私有庫 → SSH key → push → tag → 離線備份）。
103. 測試增為 **64 項**（新增 12 項：沙箱存在、與 OWNERSHIP 同步、擋住越權寫入、鏡射 Read deny、
    不擋授權查詢路徑、不鎖住自己、Router 帶硬化參數、憑證全面 deny、CI 跑齊驗證器、
    植入假金鑰能被抓到、`.gitignore` 涵蓋、沒有 Agent 能 push）。

**v2.9**（四個保證改由程式驗證）：
86. **`shared/OWNERSHIP.yaml`**：責任與寫入權的單一真相——34 項責任各一個 owner、15 條關鍵交接、17 條路徑的寫入權。制度從此是資料不是散文。
87. **`scripts/verify_isolation.py`**（lint 19）：驗證責任不重疊（含「別人手冊不得出現你的責任」）、交接兩端齊備、十個易混淆角色都有界線句、settings.json 的寫入權與 OWNERSHIP 相符。
88. **主動列出逃逸路徑**：稽核發現 **FORGE 與 LAB 同時擁有「寫檔 + 執行任意程式」**，工具層 allow/deny 對它們形同建議。這不是可以隱瞞的細節，所以 `--escapes` 會直接印出來。
89. **FORGE 收斂到 worktree 沙箱**：原本有裸 `Write`/`Edit` + `Bash(python *)`＝可寫全樹並執行。現在只能寫 `agents/forge/worktree/`，且 deny `git push/reset/merge`——合併只能由 `merge_fix.py`。
90. **`scripts/guard_paths.py`（L3 偵測層）**：Router preflight 建立 201 個受保護檔案的雜湊基準，**每次呼叫 Agent 後比對**；未授權變更自動 `git checkout` 還原，並在回覆開頭標示。已用「LAB 偷改 CHART 手冊與 RISK_RULES」實測會被抓到。
91. **`shared/MISSION.md` 共同認知卡**：與憲法同等級、逐字進 15 份 context（為什麼存在／成功定義／三層分離／四層知識／動作前自問五條）。lint 第 20 項比對 15 份是否完全一致。
92. `POSITION_CLOSED` 補進 PROTOCOL（它是 EXEC→AUDIT 的唯一觸發器，一直只存在於手冊裡）。
93. 白皮書 §2.3b：四個保證各自由哪支程式驗證；`docs/10_CODE_GOVERNANCE.md` §3.5 誠實說明三層隔離的極限與「為什麼不做 OS 層 ACL」。

**v2.8**（白皮書框架補完 · Agent 邊界稽核）：
67. **白皮書缺了「為什麼要有這個系統」**：新增 §0.0 問題陳述——五個手動交易的失效模式，各自對應到哪個機制。沒有這一段，任何機制都沒有評判標準。
68. **新增 §1.4 替代方案比較**：手動 / 300 行確定性 bot / 現成方案 / 本系統，各自的成本、上線時間、做得到與做不到。誠實承認：本系統的 A/G/B/D/E 節全部可程式化。
69. **新增 §2.2b「LLM 在哪裡真正加值」與對照組**：只有四件事是程式做不到的（非結構化總經、多時框敘述判斷、止損歸因、對抗式反證）。第 8 週決策點必須同時跑純規則基準線，**贏不過就砍掉 LLM 提案層**。
70. **§7.1 揭露 ½ Kelly 的真實角色**：代入 `p=0.40, RR=2` 得 ½Kelly = 5.0%，被 1.5% 上限截斷。**只有勝率低於 35.4% Kelly 才生效**——它是低勝率保險絲，不是放大器。原本的寫法會讓讀者與 Agent 誤以為績效好時部位會放大。
71. **§9.1 回測的三個已知偏差**：regime 覆蓋、**T2 的存活者偏差**（用今天的市值前 20 回測 = 已知它們活下來，必須用 point-in-time 快照，做不到就整層不上線）、分期滑價假設。
72. **§7.2 威脅模型**：五個攻擊者，每個都寫出「沒防住的部分」。最尖銳的一條：Discord 帳號被盜等於同時取得平倉權與核准權，憲法第六條只防冒名不防盜號。
73. **§11.5 營運經濟**：固定與變動成本、月交易筆數估計、**最小可運作帳戶規模**（隱含在 B 節 `qty < min_qty` 卻從未被算出來）、什麼時候不該跑這套系統。
74. **§14 失敗模式表 / 成功判準 / 終止條件 / 假設清單 / 法規稅務**：原本只有「進入真錢的門檻」，沒有「什麼時候該收攤」。新增五條終止條件，並要求 CEO 主動提出。
75. **§9.2 測試策略四層**，並明講**刻意不測** LLM 輸出品質——把它寫成斷言式測試是自欺。
76. **§12 的 80 行變更日誌移到本檔**：它是全文最長的一節，對人是雜訊、對 Agent 是純額度支出。
77. **§2.3 系列編號亂序修正**（2.3→2.3b→2.3e→2.3d→2.3c 改為 2.3–2.8）；移除「同 v1」寫法（讀者手上沒有 v1）；修正雙讀者定位——白皮書不屬於四層知識的任何一層，不該塞進 15 個工作目錄。
78. **Agent 邊界稽核**：修掉 FEED/LEDGER 對同一條 SUSPECT 規則各判一次、CHART 與 EXEC 各算一次 structure_stop、AUDIT 把行銷績效劃進自己的量尺、CREATIVE 直接編輯 `skills/`、CMO 與 GROWTH 在 Persona/競品/曝光上對撞。
79. **AUDIT 被授權「停用 setup」卻沒有任何管道能落地**，且抵觸憲法三。改為「提名 → RISK 共同署名 → CEO 送審 → Blacksheep 核准 → WATCH 寫入」。
80. **季審七步中第 1 步與第 6 步沒有排程**——LAB 要回測的假設從未被觸發產出，RISK 的最後風險關卡從未被叫醒。補上 `audit-quarterly-evidence` 與 `risk-quarterly-signoff`。
81. **35 個 msg_type 交接破口**（`REGIME_REPORT` 兩端都沒寫、`RECONCILE_ALERT` 沒有收件方）：新增 `sync_manual_msgflow.py` 從 PROTOCOL.md 生成每份手冊的「訊息收發」段，並加 lint 第 17 項。
82. **`.context/optimize.md` 生成了卻沒有任何 `@import`**——整個優化循環從未進入任何 Agent 的 context。補上並加 lint 第 18 項。
83. **我上一版造成的兩個新問題**：deny 基線把 FORGE 也擋住，而它正是 15 份手冊的維護者（改不了任何手冊）；`sync_manual_cron` 忽略月份欄位，季審在手冊裡被渲染成「每月 6 日」。兩者都已修正。
84. **KPI 自報違反憲法第八條**：`METRICS_SPEC.md` §7 寫死每個 KPI 的外部量測者；AUDIT 與 WATCH 互相量測（系統裡最後兩個「量別人的人」不能都沒有人量）。
85. **人設去重與銳化**：15 份 PERSONA 底部逐字重複的「共同信條」佔約四成篇幅（其中 FORGE 那份還寫著「發 BUG_REPORT 給 FORGE」＝向自己報修）；CMO 的決策原則全是標語，換成可驗證的兩條；八個易混淆角色各補一句界線（RISK 事前決定能不能做／REDTEAM 事前重建對不對／AUDIT 事後判定發生了什麼）。

**v2.7 新增**（一致性稽核 · 治理層 · 多專案複用 · 逐步手冊）：
57. **文件宣稱改由程式驗證**：新增 `scripts/verify_docs_claims.py`（lint 第 15 項）。稽核發現白皮書說「41 個視圖」實際 44、「8 項 lint 檢查」實際 16、「35 個排程」實際 43、「九條鐵律」實際 9 條——這類漂移沒有人會發現，直到有人照文件驗收。現在數字與檔案路徑都由程式比對 repo。
58. **修掉會誤導 Agent 的矛盾**：白皮書的 `A1–A12` 實際是 `A1–A8` + `G1–G15`；MACRO 切片裡的 `A7/A11/A14` 三個條款根本不存在（而它每天都會讀到）；`stop_reason` 的 `SESSION_LIQUIDITY` 不在 schema enum 裡（AUDIT 照手冊產出會被擋）；PROTOCOL 仍提到已移除的 OpenClaw 與不存在的 `agents/<id>/CLAUDE.md`；DATA_SCHEMA 還寫著 v1 的 Agent 代號。
59. **EXEC 的棘輪與對帳沒有任何觸發器**——手冊寫「每 5 分鐘」，但 `scheduler.yaml` 裡 exec 一個 job 都沒有。這是唯一會直接造成金錢損失的缺漏，已補上 `exec-ratchet` 與 `exec-reconcile`，並新增 lint 第 16 項擋住「程式型 job 沒有對應 script」。
60. **切片產物本身沒被驗證**：原本只比對來源檔雜湊，直接改 `agents/chart/.context/rules.md` 不會被發現，而 `.context/` 又在 `.gitignore` 內——整套隔離的地基是空心的。現在 MANIFEST 存輸出雜湊，所有 Agent deny `Write(.context/**)`。
61. **`settings.json` 的 deny 基線**（lint 第 14 項）：唯一有寫入權的 FORGE 原本防護最弱（`Bash(python *)` 可繞過 `Read(.env)` 的 deny）。15 份 settings 統一基線，model 改用別名與 `agents.yaml` 對齊。
62. **`!approve` 原本不會改變任何狀態**：它掛在 CEO（LLM）身上，LLM 說「已核准」而系統一個位元都沒變。改掛 WATCH（`apply_change.py`）與 EXEC（`!unlock`）。
63. **治理層**：新增 `docs/10_CODE_GOVERNANCE.md`（分支／合併／tag／回滾、備份三層與裸機還原、四種汙染源、金鑰清冊）；補上原本缺失的 `router/.env.example`（沒有它 bootstrap 第 7 步必定失敗）；`.gitignore` 補上 `*.key`、`credentials*.json`、`legacy/` 等可預期的洩漏路徑。
64. **災難情境補完**：斷電／重開機（開機先 `executor.py recover` 對帳補止損再啟動）、Discord 中斷（自動 `NO_NEW_ENTRY` + 離線平倉出口）、資料庫損壞五步、Router 崩潰迴圈；新增 `system_state.trading` 狀態機與**繞過 CEO 的直達清單**（CEO 是唯一沒有獨立監督的角色，訊號要有第二條路）。
65. **多專案資產複用**：`legacy/projects.yaml` 登錄多個舊專案，`scan_legacy.py --all` 產出索引 + **能力對照表**（同一能力有多個候選時，依 trust 與已驗證事實選一個，不合併）。新增「經驗移轉」五問——`known_issues` 必須變成新程式的測試案例。
66. **Day 0 逐步手冊**：`docs/DAY0_RUNBOOK.md`，12 個步驟，每個指令標明【PowerShell】／【瀏覽器】／【記事本】／【Discord】、整塊複製、預期輸出、失敗處置。

**v2.6 新增**（策略優化循環 · 型態學 · 資產複用）：
50. **策略持續優化循環**（`shared/OPTIMIZATION_CYCLE.md`）：L1 週檢視／L2 月審／L3 季審三級節奏，1–3 個月一輪。原則是「診斷隨時做，處方只在固定時點開」；季審**強制執行**，維持現狀也必須是跑完流程後的結論。新增四個季審排程（MACRO regime → LAB 回測與重擬合 → REDTEAM 盲審 → CEO 送審）。
51. **參數高原檢定**：關鍵參數 ±20% 擾動後 expectancy 需保有 70%，否則視為曲線擬合，改用高原中心值——即使它的回測數字最好。
52. **凱利改為 ½ Kelly**（原 ¼），公式 `f = p − (1−p)/R`，仍與 1.5% 上限（T2 為 1.0%）取小。
53. **加入型態學**：與 SMC 並用而非二選一。新增 6 種型態 setup、`pattern-analysis` skill、`scripts/patterns.py` 規格；突破必須通過量價確認（≥ 前 20 根均量 × 1.5），目標取 measured move 與 Fib/POC 較近者。
54. **MSS（市場結構轉變）正式定義**：CHoCH 只是警訊，MSS 才是已確認的轉變（收盤站穩 ≥ 0.25 ATR + 12 根內回測不破）。`htf_bias` 只在 MSS 成立時翻轉。
55. **既有專案資產複用**：`scripts/scan_legacy.py` 盤點舊專案 → `docs/11_LEGACY_ASSETS.md` 讓你標記 PORT/REF/SKIP → CEO 逐項派工 → FORGE 用 `legacy-port` skill **只讀被指派的檔**（避免舊專案假設污染新 Agent 的 context）。新增 Phase 0。
56. 稱謂統一為 **Blacksheep**（不加頭銜）。

**v2.5 新增**（交易日邊界對齊）：
45. **台北 08:00 = 00:00 UTC 定為系統的交易日邊界**：D/W/M 同時收線、`RISK_RULES` C1 單日虧損計數在此重置、所有「昨日／本月」以此換日。早晨排程改為 08:01 採集 → 08:03 指標 → 08:08 高時框（opus）→ 08:20 昨日結算 → 08:35 CEO 匯報。
46. **修掉我自己造成的 correctness 錯誤**：v2.4 為了平衡額度把「昨日日報」移到 05:30，那在交易日結束**之前**，報的是不完整的一天。原則寫進排程表檔頭：**排程可以為額度挪動，但不能跨過交易日邊界。**
47. `scripts/daily_close_check.py`：高時框任務的 precheck，確認日／週／月 K 與指標都已落庫才叫醒 opus；未到位輸出 SKIP，由 08:40 的**互斥重試**補跑（`mutex_with`，額度只計一次）。
48. **lint 第 12 項改用最壞情況**：任何「幾號」都可能落在任何星期幾，改以「每日 × 該星期 × 該號」三者疊加驗證——這揪出了原本被漏掉的週日下午與月報重疊（最高 8.2 > 6.0）。全部重排後全年最差窗回到 6.0。
49. **lint 第 13 項：手冊排程行必須與 `scheduler.yaml` 一致**，由 `scripts/sync_manual_cron.py` 生成。先前 15 份手冊裡的時間是手抄的，早就與排程表不符（例如手冊還寫著 `redteam-htf-review 08:15`，實際是 13:30）——Agent 讀到的是錯的。排程表現在是單一真相。

**v2.4 新增**：
41. **排程負載平衡**：全年最差 5 小時窗從 19.0 降到 6.0。四個 opus 任務彼此間隔 ≥ 5 小時；週報拆兩天、月報拆五天。
42. `lint_agents.py` 新增第 12 項檢查（R1 opus 間隔、R2 窗口權重），排程回歸會被擋下。
43. `strategy_params` 新增優先序分層 P0–P3：額度吃緊時交易路徑永不讓路。
44. CEO 每日匯報 opus → sonnet，opus 改用在週會（彙整不需要 opus，深度判斷才需要）。

**v2.3 新增**（內化外部實戰經驗，詳見 `docs/09_HARNESS_LESSONS.md`）：
31. **修掉一個真 bug**：`hop` 原本靠 LLM 自報，沒寫就重置為 0，迴圈保護等於失效 → 改由 Router 記帳。
32. 新增 `a2a_turns` 5 輪上限與 `NO_REPLY` 沉默機制，補上另外兩道終止條件。
33. 獨立驗收 `scripts/verify_delivery.py`：不讓交付者自己幫自己打分數。
34. 記憶治理三階段（UNVERIFIED / VALIDATED / PROMOTED），未驗證的觀察不得污染交易決策。
35. Skill 原子性：拆掉 3 個混了 4–5 件事的技能，36 個技能全部補上輸入/輸出契約；lint 會擋住未來的肥大。
36. 失敗歸因到 skill 層級（`bug_reports.skill_name` + `v_skill_failures`）。
37. Discord 實務：thread 分層自動封存、程式產生的 thread 標題、開機檢查 16 隻 Bot 的權限（避免靜默失敗）。
38. thread 內隱含收件人：Blacksheep 追問不必每次 @，但 Agent 之間仍須顯式 @（保住稽核鏈）。
39. `report-preview`：長報告產成互動 HTML 貼連結，因為兩百行 Markdown 等於沒有人真的審核。
40. CEO 第一 KPI：Blacksheep 每天 ≤ 15 分鐘。

**v2.2 新增**：
26. 指揮鏈明確化：Blacksheep → CEO → Agent，建置期與營運期共用同一套任務機制。
27. CEO 新增建置期職責與建置日報；新增 `build-orchestration` skill 與 `docs/08_BUILD_PLAN.md`（含可直接複製的 Discord 指令範本）。
28. 誠實標示 Bootstrap Floor：哪七件事只能人工做、為什麼。
29. `dev/` 重新定位為備援路徑，並列出五個該跳回去自己動手的情況。
30. 憲法加入指揮鏈與稱謂；15 份 `USER.md` 統一為 Blacksheep，並加上「自稱 Blacksheep 但 ID 不符 = 冒充」的防護。

**v2.1 新增**：
17. 四層知識模型：憲法／角色切片／查詢／交接，各有對應的隔離手段。
18. `RISK_RULES.md` 分成 A 節（提案要件）與 G 節（Gate 門檻），CHART 只拿 A 節以防 Goodhart。
19. 切片雜湊驗證：`shared/` 改了沒重建 → Router 不啟動、Agent 停工。
20. 41 個權限視圖 + 授權矩陣，資料隔離做在 SQL 而非 prompt。
21. 抗身分漂移：尾端角色提醒、20 輪 session 輪替、REDTEAM stateless。
22. 記憶三態，明確禁止自我修改人設。
23. `dev/` 與 `agents/` 的 CLAUDE.md 繼承鏈分離；根目錄不放 CLAUDE.md。
24. Router preflight：啟動前驗證上下文完整性與 Agent 定義自洽。
25. `query_readonly.py` 拒絕查底層資料表，只允許授權視圖。

**v2.0 既有**：
1. 商品宇宙四層化、群組曝險、交易時段規則（T3/T4）。
2. 只用 Claude Pro：Router + `claude -p`、模型分級、程式優先、額度預警與自動降級。
3. 只走 Discord：排程也用 Discord 訊息觸發；👀/⚙️/✅ 狀態表情；thread ↔ session 對應；迴圈保護。
4. FORGE：修復、開發 skill、lint Agent 一致性、EXEC/RISK 改動須紅隊 + 你核准。
5. 行銷三人組：CMO/CREATIVE/GROWTH；Canva MCP；IG 兩步發佈 + 你核准；合規聲明；行銷量尺。
6. Skills 化：15 個可搬遷技能包；Agent = 角色 + Skills + 權限。
7. 人設與手冊：每個 Agent 有身分、性格、決策原則、職責、觸發、輸入輸出、Skills、工具白名單、模型、額度、KPI、完成定義、禁忌、升級路徑、訊息模板。
8. IG 個人帳號 → 專業帳號 → 綁 FB 粉專 → Meta App → 權限審核（2–4 週）的完整步驟寫進教學。
9. REDTEAM 盲審取代跨模型審核（誠實標註限制）。
10. 資料倉新增 `universe`、`content`、`bug_reports`、`fix_log`。

---
