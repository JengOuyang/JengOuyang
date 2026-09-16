# Day 0 逐步操作手冊（一鍵複製版）

> **這份文件的規則**：每一步都標明【在哪裡操作】，指令一律是**整塊複製貼上**，並附**預期看到什麼**與**失敗怎麼辦**。
> 你不需要理解指令內容，照順序做完就會有一個活著的 CEO。
> 全程約 **60–90 分鐘**，其中 Discord 建 Bot 佔一半。

**四個操作場所**（後面用這四個標籤）：

| 標籤 | 意思 |
|---|---|
| 【PowerShell】 | Windows 開始 → 打 `powershell` → 開啟的藍色視窗。**整段複製貼上後按 Enter** |
| 【瀏覽器】 | Chrome / Edge，操作 Discord 網站 |
| 【記事本】 | PowerShell 會自動幫你開啟，填完存檔關閉 |
| 【Discord】 | Discord 應用程式或網頁，在指定頻道貼訊息 |

---

## 步驟 0｜確認隔離層級（Windows 原生）【PowerShell】

**你選的是 Windows 原生，這份手冊就以它為準。** 這一步只要複製一塊指令，
但先花兩分鐘知道你拿到的是什麼、沒拿到的是什麼。

Claude Code 的作業系統層沙箱（`docs/12_DIGITAL_BOUNDARY.md` 的 L0）
用的是 Linux 的 bubblewrap 與 macOS 的 Seatbelt，**原生 Windows 沒有對應機制**。
所以你的系統會跑在三層隔離上，而不是四層：

| 層 | 在你的環境 | 擋得住什麼 |
|---|---|---|
| L0 OS 沙箱 | ❌ 不存在 | — |
| L1 工具層 | ✅ | 15 份 `settings.json` 的 allow/deny：13 個 Agent 完全擋死；所有人對 `shared/`、`.context/`、`.env`、`data/` 的直接寫入 |
| L2 執行層 | ✅ | FORGE 只能寫自己的 worktree、LAB 只能寫 `backtest/`；合併只有 `merge_fix.py` 做得到 |
| L3 偵測層 | ✅ | 每次呼叫後比對 201 個受保護檔案的 SHA-256，未授權變更**自動 `git checkout` 還原 + HALT + @你** |

**白話**：FORGE 與 LAB 這兩個必須「能寫檔又能執行程式」的 Agent，
理論上能寫一支腳本再執行它來繞過 L1。在 Windows 上這件事**擋不住，但 30 秒內會被抓到並自動還原**，
而且系統會停下來叫你。對單人系統來說這是可接受的取捨——
真正會虧錢的路徑（下單、寫資料倉、改風控規則）全部是程式在把關，不在這一層。

複製這一塊確認設定正確：

```powershell
$env:TD_REQUIRE_SANDBOX="0"
python -c "print('L0 沙箱：關閉（Windows 原生）；隔離 = L1 + L2 + L3')"
```

`TD_REQUIRE_SANDBOX=0` 是預設值，步驟 7 填 `router/.env` 時會再寫一次，這裡只是先讓你知道它存在。

> **之後想升級成四層的話**（不急，系統跑順了再說）：
> Windows 內建的 WSL2 就能跑 L0——它是 Windows 的一個功能，不是換作業系統，
> 你的 Windows 桌面、Discord、瀏覽器完全不受影響，只是專案檔案搬到
> `\\wsl$\Ubuntu-24.04\home\<你>\trade-desk`（檔案總管照樣打得開）。
> 步驟如下，**現在可以完全跳過**：
> ```powershell
> wsl --install -d Ubuntu-24.04      # 裝完要重開機
> ```
> ```bash
> sudo apt-get update && sudo apt-get install -y bubblewrap socat python3.12 python3-pip git
> sysctl kernel.apparmor_restrict_unprivileged_userns   # 回傳 1 的話見 docs/12_DIGITAL_BOUNDARY.md
> ```
> 然後把 `router/.env` 的 `TD_REQUIRE_SANDBOX` 改成 `1`。Router 啟動時會確認沙箱真的在。

---

## 步驟 1｜安裝執行環境 【PowerShell】

先裝三個東西（若已有可跳過）：Python 3.12（安裝時**務必勾選 Add Python to PATH**）、Node.js LTS、Git。
下載頁：python.org/downloads、nodejs.org、git-scm.com

裝完後複製這一塊：

```powershell
python --version; node --version; git --version
```

**預期看到**：三行版本號，例如 `Python 3.12.x`。
**失敗怎麼辦**：出現「無法辨識」= 沒裝或沒勾 Add to PATH → 重裝那一個，勾選 PATH，然後**關掉 PowerShell 重開**。

---

## 步驟 2｜安裝 Claude Code 並登入 【PowerShell】

```powershell
irm https://claude.ai/install.ps1 | iex
```

接著：

```powershell
claude
```

Claude Code 會開起來。**在 claude 裡面**依序打這三行（一行一行打，不是複製整塊）：

```
/login
/model
/exit
```

`/login` 會開瀏覽器讓你用 Claude Pro 帳號登入。`/model` 會顯示可用的模型別名，**記下來**（通常是 haiku / sonnet / opus）。

回到 PowerShell 後，驗證非互動模式可用：

```powershell
claude -p "回覆 OK" --output-format json --model sonnet
```

**預期看到**：一段 JSON，裡面有 `"result":"OK"`。
**失敗怎麼辦**：出現 401 或要求登入 → 重跑 `claude` → `/login`。**這一步不過，後面全部不用做**——Router 就是靠這個指令驅動 15 個 Agent。

---

## 步驟 2B｜驗證 `claude -p` 真的能跑 【PowerShell】

**這是整套系統的地基。** Router 不是用互動模式跟 Agent 講話，它用的是
`claude -p`（非互動、一問一答、輸出 JSON）。這件事若不成立，Router 會**沉默地卡住**
——它在等 stdout，而不是報錯。所以在裝任何東西之前先驗它。

複製這一塊：

```powershell
claude -p "回覆 OK" --output-format json --model sonnet
```

**預期看到**：等 10～60 秒（第一次比較久），然後**一次吐出一整包 JSON**，裡面有
`"result":"OK"`、`"is_error":false`、`"session_id":"..."`。

> ⚠️ **最常被誤判成「沒反應」的情況**：`--output-format json` **不會邊跑邊印**。
> 畫面在跑完之前是完全空白的，看起來就像當掉。先等滿 60 秒再說。

**真的沒反應的話，照順序試：**

| 症狀 | 原因 | 怎麼辦 |
|---|---|---|
| 完全空白、游標一直閃、按 Ctrl+C 才回到提示字元 | **還沒登入** | 先打 `claude` 進互動模式完成 `/login`，`/exit` 之後再回來重試 |
| 一樣空白，但你**沒有**在指令裡給提示詞 | `claude -p` 不帶提示詞時會**讀 stdin**，你沒給它就永遠等 | 把提示詞當參數：`claude -p "回覆 OK"` |
| `claude : 無法辨識...` | PATH 沒生效 | **關掉 PowerShell 重開**（裝完一定要重開）；還是不行就打 `where.exe claude` 確認位置 |
| `因為這個系統上已停用指令碼執行` | npm 版的 PowerShell 包裝腳本被執行原則擋住 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 後重開，或改用 `claude.cmd` |
| 跑出 JSON 但 `"is_error":true` | 額度用完或網路被擋 | 看 `result` 欄位的訊息；公司網路 / VPN 常擋 `api.anthropic.com` |
| 中文變成亂碼 | PowerShell 編碼 | `chcp 65001`，或改用 Windows Terminal |

**把這一步自動化**（部署完專案之後隨時可以重跑）：

```powershell
python scripts\doctor.py
```

它會把上面這些全部驗一遍——工具版本、`claude -p` 冒煙測試（含逾時診斷）、
專案五個驗證器、`.env` 缺哪幾個鍵、目前的隔離層級——並明確告訴你能不能開工。

---

## 步驟 3｜部署專案 【PowerShell】

### 先決定放在哪裡——這一步選錯，之後會反覆咬你

把 `trade-desk.zip` 解壓到 **`C:\trade-desk`**。三個硬性要求：

| 要求 | 為什麼 |
|---|---|
| **路徑不能有空格** | `C:\Users\你\Desktop\My AI Agent\...` 這種路徑會讓 `pip.exe`、`claude.cmd` 這類啟動器在引號處理上出問題 |
| **不要放桌面或「文件」** | 那兩個資料夾通常被 OneDrive 同步。45 個排程任務每天讀寫，加上 SQLite 資料庫，同步程式會鎖檔、製造衝突副本，**資料庫損毀是真的會發生** |
| **不要放在中文資料夾下** | 部分工具的編碼處理仍不完整 |

解壓後應該看得到 `router`、`agents`、`shared`、`docs`、`scripts` 這些資料夾，
以及根目錄的 `requirements.txt`。

### 建立虛擬環境

```powershell
cd C:\trade-desk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**預期看到**：提示字元前面多出 `(.venv)`，以及一連串 `Successfully installed ...`。

> **為什麼用 `python -m pip` 而不是 `pip`**：`pip.exe` 是個啟動器，裡面**寫死了建立當下的
> python.exe 絕對路徑**。只要 `.venv` 被搬走、改名，或上層資料夾改過名字，它就會報
> `Fatal error in launcher: Unable to create process using ...`。
> `python -m pip` 用的是當前這個 python，不看那串寫死的路徑，所以不會有這個問題。

**失敗怎麼辦**：

| 訊息 | 原因 | 怎麼辦 |
|---|---|---|
| `無法載入檔案 ... 執行原則` | PowerShell 擋住 `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 後重來 |
| `Fatal error in launcher: Unable to create process using ...` | **`.venv` 被搬過家**（venv 不可搬移） | 刪掉重建，見下面那一塊 |
| `找不到檔案 requirements.txt` | 跑錯目錄，或以為它在 `router\` | 它在**專案根目錄**；先 `cd C:\trade-desk` |

**`.venv` 搬過家的修法**（整塊複製，安全，不會動到你的程式碼）：

```powershell
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`.venv` 只是套件的快取，砍掉重建沒有任何損失。**永遠不要搬移或改名一個已經建好的 venv。**

### 初始化

```powershell
python scripts\build_context.py
python scripts\init_db.py
python scripts\doctor.py --no-claude
```

**預期看到**：切片重建完成、資料庫建立完成，最後 `doctor` 印出
「✅ 可以開工」或「✅ 可以開工（N 個警告）」。
**失敗怎麼辦**：`doctor` 出現 ❌ 就**停下來照它說的修**，不要往下做——
它每一條都附了處置方式。

### 安裝技能

```powershell
mkdir $HOME\.claude\skills -Force
Copy-Item -Recurse -Force skills\* $HOME\.claude\skills\
```

（版本控制在下一步 3B 一併做——**必須先裝好金鑰閘門再 commit**，順序不能顛倒。）

---

## 步驟 3B｜接上 GitHub 與本機防護 【PowerShell】

**為什麼現在做而不是最後**：金鑰一旦被 commit 進歷史就等於外洩，改 commit 也救不回來
（要去 Bitget / Discord 撤銷重發）。所以金鑰閘門要在**第一個 commit 之前**裝好。

複製這一塊：

```powershell
git init -b main
python scripts/install_git_hooks.py
python scripts/check_secrets.py --all
git add -A
git commit -m "TRADE-DESK v3.0 初始版本"
python scripts/check_secrets.py --history
```

**預期看到**：`已安裝 .git/hooks/pre-commit`（三行）、`沒有發現金鑰`（兩次）、一行 commit 摘要。
**失敗怎麼辦**：如果 `check_secrets` 抓到東西，**不要跳過**——把那個值搬進 `router/.env`
（已在 `.gitignore`），程式改讀環境變數，再跑一次。

接著【瀏覽器】到 github.com → 右上 `+` → New repository：
- Repository name：`trade-desk`
- **Private**（一定要，這個庫裡有你的策略參數與風控規則）
- 三個勾選框（README / .gitignore / license）**全部不要勾**

建好後回到【PowerShell】，把 `<你的帳號>` 換成你的 GitHub 帳號，複製這一塊：

```powershell
ssh-keygen -t ed25519 -C "trade-desk" -f $HOME\.ssh\id_ed25519 -N '""'
Get-Content $HOME\.ssh\id_ed25519.pub | Set-Clipboard
```

**預期看到**：金鑰產生訊息；公鑰已複製到剪貼簿。
【瀏覽器】到 GitHub → 右上頭像 → Settings → SSH and GPG keys → New SSH key → 直接貼上 → Add。

回到【PowerShell】：

```powershell
ssh -T git@github.com
git remote add origin git@github.com:<你的帳號>/trade-desk.git
git push -u origin main
git tag -a v3.0-build -m "15 Agent 建置完成；尚未接實盤"
git push origin v3.0-build
```

**預期看到**：`successfully authenticated`、推送進度、`* [new tag]`。
**失敗怎麼辦**：`Permission denied (publickey)` = SSH key 沒貼成功或貼錯帳號 → 重做上一段。

最後做第一份離線備份（把 `D:\backup` 換成你實際的備份碟或雲端同步資料夾）：

```powershell
python scripts/backup_mirror.py --to D:\backup\trade-desk
```

**為什麼還要這一步**：GitHub 是遠端副本不是備份——帳號被停權、倉庫被誤刪、
force-push 覆蓋歷史的時候它會跟著一起消失。完整說明見 `docs/13_GITHUB.md`。

> **之後的日常**：`pre-commit` 會自動跑金鑰掃描與 lint，`pre-push` 會跑完整驗證。
> 你不需要記得跑它們。每週跑一次 `python scripts/backup_mirror.py --to <你的備份碟>` 就好。

---

## 步驟 4｜盤點你的舊專案 【PowerShell】+【記事本】

你已經有好幾個能用的專案，先讓系統知道它們在哪，之後 CEO 才能安排複用而不是重寫。

```powershell
Copy-Item legacy\projects.yaml.example legacy\projects.yaml
notepad legacy\projects.yaml
```

【記事本】把每個舊專案填進去（`path` 填實際資料夾路徑），**特別把 `proven`（已驗證的事實）與 `known_issues`（踩過的坑）寫清楚**——這兩欄決定 CEO 會不會選對來源。填完存檔關閉。

```powershell
python scripts\scan_legacy.py --all
notepad docs\11_LEGACY_ASSETS.md
```

【記事本】在「能力對照表」的**你的決定**欄填來源代號。存檔關閉。

**預期看到**：PowerShell 印出每個專案掃到幾個檔、幾種能力，以及有沒有檔案疑似含金鑰。
**失敗怎麼辦**：「找不到路徑」→ 回去改 `legacy\projects.yaml` 的 `path`（Windows 路徑用反斜線，不用加引號）。

> 這一步可以跳過，之後任何時候再做都行。但**越早做越省事**——它可能直接抵掉 Phase 2–6 的一半待辦。

---

## 步驟 5｜建立 Discord 伺服器與頻道 【瀏覽器】

1. Discord 左側 `+` → **建立我的伺服器** → 名稱 `TRADE-DESK` → 建立。
2. 開啟開發者模式：**使用者設定 → 進階 → 開發者模式** 打開（之後才能右鍵複製 ID）。
3. 建立 18 個頻道。分類與頻道名稱照 `docs/03_DISCORD_SETUP.md` 的表；**Day 0 先建這 6 個就能跑**：

```
human-inbox
ceo-daily
tasks
macro
agent-health
alerts
```

其餘 12 個之後再建（CEO 會提醒你）。

---

## 步驟 6｜建立前 2 隻 Bot 【瀏覽器】

**Day 0 只建 2 隻：`TD-ROUTER` 與 `TD-CEO`。** 其餘 14 隻讓 CEO 帶你建。

對每一隻重複以下**七**個動作。**第 4、5 步的順序不能顛倒**（見下方失敗排除）。

1. 開 https://discord.com/developers/applications → **New Application** → 名稱填 `TD-ROUTER`（第二輪填 `TD-CEO`）→ Create
2. 左側 **Bot** 頁 → **Reset Token** → **Copy**（token 只會顯示一次，先貼到記事本暫存）
3. 同一頁往下：開啟 **MESSAGE CONTENT INTENT** 與 **SERVER MEMBERS INTENT**（兩個都要開）→ **Save Changes**
4. 左側 **Installation（安裝）** → **Install Link（安裝連結）** 選 **None（無）** → **Save Changes**
5. 回到左側 **Bot** → **PUBLIC BOT 關閉** → **Save Changes**（不然別人可以邀請你的 Bot）
6. 左側 **OAuth2 → URL Generator** → SCOPES 那份長長的清單裡**只勾 `bot` 一個** → 下方冒出的 BOT PERMISSIONS 勾這九個：
   `View Channels`、`Send Messages`、`Send Messages in Threads`、`Create Public Threads`、
   `Read Message History`、`Attach Files`、`Embed Links`、`Add Reactions`、`Manage Threads`
7. 複製頁面最下方產生的網址 → 貼到瀏覽器 → 選 `TRADE-DESK` 伺服器 → 授權

**預期看到**：伺服器成員清單出現 `TD-ROUTER` 與 `TD-CEO`（離線狀態，正常）。

**失敗怎麼辦**：

| 訊息 / 症狀 | 原因 | 怎麼辦 |
|---|---|---|
| 關 Public Bot 時跳「私人應用程式不得使用預設授權連結」 | 先關了 Public Bot 才處理安裝連結 | 照第 4 步先把 **Installation → Install Link 設成 None** 並存檔，再回來關 |
| Install Link 存不成 None，訊息提到 discoverable / 探索 | 這個應用程式開了 App Discovery | 左側 **App Discovery** 頁最下方 **Disable Discovery**，再回第 4 步 |
| Scopes 清單有二十幾個看不懂的選項 | 那是 Discord 的完整清單，每個應用程式都一樣 | **只勾 `bot`**，其餘全部不勾。本專案不用斜線指令，所以連 `applications.commands` 都不需要 |
| Bot 上線但完全不回應 | **忘記開 MESSAGE CONTENT INTENT** | 這是最常見的錯。回第 3 步確認兩個 Intent 都開了且按過 Save |

最後複製三種 ID（右鍵 → 複製 ID，先貼記事本）：

- 伺服器 ID：右鍵伺服器圖示
- 你自己的 User ID：右鍵你的頭像
- 6 個頻道 ID：右鍵各頻道

---

## 步驟 7｜填設定檔 【PowerShell】+【記事本】

```powershell
cd C:\trade-desk
Copy-Item router\.env.example router\.env
notepad router\.env
```

【記事本】填入（其他先留空）：

```
OWNER_USER_ID=<你的 Discord User ID>
GUILD_ID=<伺服器 ID>
DISCORD_TOKEN_ROUTER=<TD-ROUTER 的 token>
DISCORD_TOKEN_CEO=<TD-CEO 的 token>
CH_HUMAN_INBOX=<#human-inbox 的頻道 ID>
CH_CEO_DAILY=<#ceo-daily 的頻道 ID>
CH_TASKS=<#tasks 的頻道 ID>
CH_MACRO=<#macro 的頻道 ID>
CH_AGENT_HEALTH=<#agent-health 的頻道 ID>
CH_ALERTS=<#alerts 的頻道 ID>
```

存檔關閉，然後收緊權限並填 CEO 的 USER.md：

```powershell
icacls router\.env /inheritance:r /grant:r "$env:USERNAME:(R,W)"
notepad agents\ceo\USER.md
```

【記事本】把 `Owner Discord User ID：<填入你的 Discord User ID...>` 換成你的實際 ID。存檔關閉。

最後暫時只留兩隻 Bot（整塊複製）：

```powershell
python - <<'PY'
import re, pathlib
p = pathlib.Path("router/agents.yaml"); s = p.read_text(encoding="utf-8")
p.with_suffix(".yaml.full").write_text(s, encoding="utf-8")   # 完整版備份，之後還原用
keep, out, cur = {"router", "ceo"}, [], None
for line in s.splitlines():
    m = re.match(r"^  (\w+):\s*$", line)
    if m: cur = m.group(1)
    out.append(line if (cur is None or cur in keep) else ("# " + line))
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("已暫時停用其餘 13 個 Agent（完整版備份在 router/agents.yaml.full）")
PY
```

---

## 步驟 8｜啟動 【PowerShell】

先健檢一次（**每次覺得怪怪的都可以重跑這一行**）：

```powershell
python scripts\doctor.py
```

**預期看到**：最後一行是「✅ 全部通過，可以啟動 Router」或
「✅ 可以開工（N 個警告）」。出現 ❌ 就照它說的修，不要硬開。


```powershell
cd C:\trade-desk
.\.venv\Scripts\Activate.ps1
python router\discord_router.py
```

**預期看到**：preflight 通過的訊息，接著 `TD-ROUTER`、`TD-CEO` 在 Discord 變成上線（綠點）。
**這個視窗要一直開著**——關掉 Router 就停了。之後再設定成開機自動啟動（`docs/02_SETUP_GUIDE.md` §9）。

**失敗怎麼辦**：

| 訊息 | 原因 | 處置 |
|---|---|---|
| `preflight 失敗` | 切片或 lint 沒過 | 回步驟 3 重跑 `build_context.py` |
| `PrivilegedIntentsRequired` | 忘了開 Intent | 回步驟 6 第 3 點 |
| `Improper token` | token 貼錯或多了空白 | 重 Reset Token 再貼一次 |
| 缺少權限 | 邀請時漏勾 | 重跑步驟 6 第 5 點的邀請網址 |

---

## 步驟 9｜確認 CEO 活著 【Discord】

到 `#human-inbox` 貼這一行：

```
@TD-CEO !status
```

**預期看到**：訊息出現 👀 → ⚙️ → CEO 開一個 thread 回覆 → ✅

到這裡 **Bootstrap Floor 就結束了**。你不用再碰終端機（除了緊急狀況）。

---

## 步驟 10｜交棒給 CEO 【Discord】

在 `#human-inbox` 貼這一整段：

```
@TD-CEO 我是 Blacksheep。Router 已上線，目前只有 TD-ROUTER 與 TD-CEO 兩隻 Bot。
請讀 docs/08_BUILD_PLAN.md 與 docs/11_LEGACY_ASSETS.md，回報四件事：
(1) 目前在哪個 Phase
(2) 下一步該做什麼
(3) 有沒有需要我先決定的事
(4) 我標記 PORT 的既有資產中，哪些可以直接抵掉 Phase 2-6 的待辦
```

---

## 步驟 11｜讓 CEO 帶你建完其餘 14 隻 Bot 【Discord】

```
@TD-CEO 我要建剩下 14 隻 Bot。請一次只給我一隻的完整步驟
（Application 名稱、要開哪些 Intent、要勾哪些權限、token 要填到 .env 的哪個變數名），
我做完回「done」你再給下一隻。
```

14 隻都建完後，回到【PowerShell】還原完整設定並重啟：

```powershell
cd C:\trade-desk
Copy-Item router\agents.yaml.full router\agents.yaml -Force
python scripts\lint_agents.py
python router\discord_router.py
```

---

## 步驟 12｜之後的日常 【Discord】

你只需要這三種指令：

```
@TD-CEO 開始 Phase 2
```
```
@TD-CEO !status
```
```
!approve FIX-2026-0912-003
```

其餘由 CEO 派工、FORGE 實作、REDTEAM 與 RISK 審核。每天早上 08:35 看 `#ceo-daily` 的日報，約 3 分鐘。

---

## 附：什麼時候該回到 PowerShell

| 情況 | 指令 |
|---|---|
| 改了 `shared/` 的規格 | `python scripts\build_context.py` 然後重啟 Router |
| 改了 `scheduler.yaml` | `python scripts\sync_manual_cron.py` + `python scripts\lint_agents.py` 然後重啟 |
| 想確認系統自洽 | `python scripts\lint_agents.py` |
| 緊急平倉（Discord 掛掉時） | `python engine\executor.py flatten --local` |
| 想自己動手改程式 | `cd dev`（見 `docs/04_DEV_ENVIRONMENT.md`） |
