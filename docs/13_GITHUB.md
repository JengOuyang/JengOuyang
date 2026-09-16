# 13　GitHub：要不要用、怎麼用、用來做什麼

> 我的建議先給結論：**要用，但只用三件事，而且不要把它當備份。**

---

## 一、先回答「要不要」

要。理由不是「大家都用」，而是這個專案有三個特徵讓 GitHub 的價值特別高：

| 特徵 | 沒有 GitHub 會怎樣 |
|---|---|
| 15 個 Agent 會自動改程式（FORGE 修 bug、sync_* 重生成手冊） | 改壞了只能靠記憶回推；`git log` 是唯一能回答「昨天誰動了 RISK_RULES」的東西 |
| 單人開發，沒有 code reviewer | 沒有任何一雙第二隻眼睛；CI 是唯一能在你累的時候說「不對」的角色 |
| 碰真錢 | 需要「這個版本在實盤跑了三週」這種不可竄改的時間戳；`git tag` 就是 |

反方向也要講清楚：**GitHub 不會讓你的系統更安全。**
Free 方案的私有庫沒有分支保護、沒有 secret scanning（下面第三節），
所以它提供的是**紀錄**與**自動驗證**，不是**強制**。強制那一層在你本機的 git hook 裡。

---

## 二、用來做什麼（只有三件事）

### 1. 版本歷史與回滾 —— 最重要的一件

這個系統最危險的失效不是崩潰，是**無聲的漂移**：
某次 FORGE 的修復把 `strategy_params.yaml` 的 ATR 倍數從 1.5 改成 1.2，
你兩週後才發現止損變密、勝率掉了。

沒有版本控制，你無法回答「什麼時候變的」。有的話：

```bash
git log -p --follow shared/strategy_params.yaml     # 這個檔的每一次變更與當時的理由
git bisect start                                    # 二分搜尋「哪一次 commit 開始壞的」
```

`docs/10_CODE_GOVERNANCE.md` 已經定義了分支模型（只有 `merge_fix.py` 能寫 `main`）與標籤規則。
GitHub 只是讓這件事有一份不在你這台電腦上的副本。

### 2. GitHub Actions 當 CI —— 你唯一的 reviewer

`.github/workflows/ci.yml` 每次推送都跑：

```
金鑰掃描（工作區 + 全歷史）
  → build_context.py（.context/ 不進版控，CI 自己生）
  → lint_agents.py（33 項）
  → verify_isolation.py（職責 / 交接 / 權限 / OS 沙箱）
  → verify_docs_claims.py（文件說 44 個視圖，實際就得是 44 個）
  → pytest（170 項）
```

它還有一條 `schedule: "0 1 * * 1"`（每週一 09:00 台北）——
**沒有推送也驗一次**。這是為了抓「環境腐化」：相依套件升級、Python 版本變動、
或者某個生成器的輸出因為外部原因變了。單人專案最容易死在這種地方。

私有庫在 Free 方案每月有 2000 分鐘 Actions 額度，這個工作流一次約 1–2 分鐘。
就算每天推 10 次也用不到十分之一。

### 3. `git tag` 標記「這個版本跑過實盤」

```bash
git tag -a live-2026-09-15 -m "Gate B 通過；ETH/BTC 4H；實盤第 1 週"
git push origin live-2026-09-15
```

AUDIT 的季度回顧、LAB 的參數提名，都需要「當時跑的是哪一版」。
tag 是唯一不會說謊的答案。`docs/10_CODE_GOVERNANCE.md` §2 有完整的標籤命名規則。

---

## 三、Free 方案的私有庫少了什麼（這點很多文章沒講清楚）

我查證過目前的狀態：

| 功能 | 公開庫 | 私有庫（Free 方案） |
|---|---|---|
| Actions CI | 免費（無限） | 免費 2000 分鐘/月 ✅ |
| 分支保護 / rulesets | 免費 | **不可用**（需 Team 以上）❌ |
| Secret scanning + push protection | 免費 | **需付費**（GitHub Secret Protection，按 active committer 計費）❌ |
| Dependabot 安全更新 | 免費 | 免費 ✅ |

GitHub 社群討論串裡有多筆請願要求把基本分支保護開放給 Free 方案的私有庫，
官方回覆是「會轉給產品團隊」，沒有承諾
（[community#190190](https://github.com/orgs/community/discussions/190190)、
[community#174400](https://github.com/orgs/community/discussions/174400)）。

**這對本專案的意義是：伺服器端擋不住你自己，所以防線必須在本機。**

`scripts/install_git_hooks.py` 裝三個鉤子：

```bash
python scripts/install_git_hooks.py
```

| 鉤子 | 做什麼 | 為什麼 |
|---|---|---|
| `pre-commit` | `check_secrets.py` + `lint_agents.py` | 金鑰是不可逆的；設定漂移是最常見的失效 |
| `pre-push` | `verify_isolation.py` + `verify_docs_claims.py` + `pytest` | 本機先知道比等 CI 便宜 |
| `post-commit` | 提醒鏡像備份 | 見下一節 |

`scripts/check_secrets.py` 是自己寫的 push protection 替代品，
涵蓋 Discord bot token、Anthropic / OpenAI key、AWS key、GitHub token、
Notion token、私鑰區塊，以及 `api_secret = "..."` 這類交易所憑證樣式。
它有 `--history` 模式：**第一次推上 GitHub 之前一定要跑一次**，
確認歷史裡沒有金鑰（歷史裡的金鑰推上去就等於外洩，改 commit 也救不回來——
要做的是去 Bitget / Discord 撤銷重發）。

**絕對不要用私有庫當作「反正沒人看得到」的理由。**
私有庫的內容一樣會被你的 CI、你安裝的 Action、任何有 read 權限的協作者看到。
`router/.env` 永遠不進版控，`.gitignore` 第一段就是這個。

---

## 四、GitHub 不是備份

這句話在開發者圈子被反覆講，因為反覆有人踩：帳號被停權、倉庫被誤刪、
force-push 覆蓋了歷史、或單純是「我以為 GitHub 有幫我備份」。
GitHub 的服務條款本身也不承諾保存你的資料。

git 的分散式特性讓每個 clone 都是完整歷史——**但前提是你真的有另一份 clone**。

`scripts/backup_mirror.py` 做 3-2-1 的第 2、3 份：

```bash
python scripts/backup_mirror.py --to /mnt/d/backup/trade-desk
```

它做三件事：
1. `git bundle create --all` 打包整個歷史成單一檔案（可丟雲端硬碟 / 隨身碟，`git clone` 就能還原）
2. `git clone --mirror` 到另一個實體位置
3. 匯出「不進版控但不能丟」的清單：`router/.env` 的**鍵名**（不含值）、資料庫大小與備份指令

第 3 點很重要。災難還原的時候，最卡人的不是程式碼——程式碼在 git 裡好好的——
是「我當初 .env 裡到底要放哪幾個鍵」。值本身請放密碼管理器，不要放備份檔。

**資料庫另外算。** `data/tradedesk.db` 不進 git（太大、變動太頻繁、而且是資料不是程式碼）：

```bash
sqlite3 data/tradedesk.db ".backup 'D:/backup/tradedesk-$(date +%Y%m%d).db'"
```
建議排進 `scheduler.yaml`，每日收線後（台北 08:10）跑一次。

---

## 五、Day 0 該打的指令（一鍵複製）

在 **PowerShell** 裡，專案目錄下依序執行。完整版含預期輸出與失敗處置見 `DAY0_RUNBOOK.md` 步驟 3B。

```powershell
git init -b main
python scripts/install_git_hooks.py
python scripts/check_secrets.py --all
git add -A
git commit -m "TRADE-DESK v3.0 初始版本"
python scripts/check_secrets.py --history
```

【瀏覽器】在 github.com 建一個 **Private** 倉庫，名字 `trade-desk`，
「Add a README」「.gitignore」「license」三個都**不要勾**（我們已經有了）。

回到 PowerShell，沒設過 SSH key 的話先做這段：

```powershell
ssh-keygen -t ed25519 -C "trade-desk" -f $HOME\.ssh\id_ed25519 -N '""'
Get-Content $HOME\.ssh\id_ed25519.pub | Set-Clipboard
```

【瀏覽器】GitHub → 頭像 → Settings → SSH and GPG keys → New SSH key → 貼上 → Add。
然後把 `<你的帳號>` 換掉：

```powershell
ssh -T git@github.com
git remote add origin git@github.com:<你的帳號>/trade-desk.git
git push -u origin main
git tag -a v3.0-build -m "15 Agent 建置完成；尚未接實盤"
git push origin v3.0-build
python scripts/backup_mirror.py --to D:\backup\trade-desk
```

用 SSH 而不是 HTTPS，是為了不必在本機存 personal access token
（存了就是一個會被 Agent 讀到的金鑰）。

> **關於這把私鑰**：在 WSL2 / macOS / Linux 上，`~/.ssh` 是每個 Agent 沙箱設定裡的
> `credentials.files` deny，Agent 的 Bash 子程序讀不到它。
> **原生 Windows 沒有這層保護**——所有 Agent 跑在你的使用者身分下，
> 檔案系統層面讀得到 `%USERPROFILE%\.ssh`。工具層的 deny 擋得住 `Read` 工具，擋不住 Bash。
> 緩解：這把 key 只給 GitHub 用、不重用在別處；`docs/12_DIGITAL_BOUNDARY.md` 第四節有完整取捨。

---

## 六、我不建議做的事

| 不建議 | 為什麼 |
|---|---|
| 把倉庫設成 public 以換取免費的 secret scanning 與分支保護 | 你的 `strategy_params.yaml`、`RISK_RULES.md`、`OPTIMIZATION_CYCLE.md` 就是這個系統的全部價值 |
| 升級到 GitHub Team 只為了分支保護 | 單人專案用不到「擋住別人」；本機 hook + CI 紀錄已經涵蓋你真正的失效模式 |
| 讓某個 Agent 有 `git push` 權 | FORGE 目前明確 deny `Bash(git push *)`。一旦 Agent 能推遠端，L2 的「合併必須經 merge_fix.py」就繞過了 |
| 在 GitHub 存任何交易資料或 API 憑證 | `data/` 與 `router/.env` 都在 `.gitignore`；`check_secrets.py` 是第二道 |
| 用 GitHub Actions 跑回測或接交易所 | CI runner 拿不到（也不該拿到）你的憑證；回測是 LAB 在本機的工作 |

---

## 參考

- [GitHub is not a backup (And Why That Matters)](https://www.holgerscode.com/blog/2025/12/30/github-is-not-a-backup-and-why-that-matters/)
- [GitHub Is Not Your Backup. One Suspended Account Proved It This Week.](https://dev.to/rentierdigital/github-is-not-your-backup-one-suspended-account-proved-it-this-week-2fb3)
- [Rulesets Free Plan Private Repo — GitHub community#190190](https://github.com/orgs/community/discussions/190190)
- [Please Make Basic Branch Protection Free for Private Repositories — community#174400](https://github.com/orgs/community/discussions/174400)
- [GitHub Secret Scanning 2026: Free for Public Repos](https://appsecsanta.com/github-secret-scanning)
- [GitHub Push Protection: Benefits and Key Limitations](https://blog.gitguardian.com/github-push-protection-enhancing-open-source-security-with-limitations-to-consider/)
- [The Ultimate Developer's Guide to GitHub Backups](https://simplebackups.com/blog/the-ultimate-developers-guide-to-github-backups)
- 本專案：`docs/10_CODE_GOVERNANCE.md`（分支 / 標籤 / 回滾）、`docs/12_DIGITAL_BOUNDARY.md`（Agent 邊界）
