# QUICKSTART — 30 分鐘讓第一個 Agent 在 Discord 上回應你

> **需要一步一步、可直接複製貼上的版本？看 `docs/DAY0_RUNBOOK.md`**——每個指令都標明在哪裡輸入、預期看到什麼、失敗怎麼辦。
> 本檔是給已經熟悉環境的人看的濃縮版。

完整版見 `docs/02_SETUP_GUIDE.md`（18 節）。這裡只做「最小可運行」：1 隻 Bot、1 個 Agent、1 則訊息。

## 0. 前置（各一次）
```powershell
# Python 3.12（安裝時勾 Add to PATH）、Node LTS、Git
PS> irm https://claude.ai/install.ps1 | iex
PS> claude
claude> /login          # 用 Claude Pro 帳號
claude> /model          # 記下可用模型別名
claude> /exit
PS> claude -p "回覆 OK" --output-format json --model sonnet    # 應回傳含 "result":"OK" 的 JSON
```

## 1. 部署
```powershell
PS> # 解壓 trade-desk.zip 到 C:\trade-desk
PS> cd C:\trade-desk
PS> python -m venv .venv; .\.venv\Scripts\Activate.ps1
PS> pip install -r router\requirements.txt
PS> python scripts\build_context.py        # 生成 15 個 Agent 的規則切片
PS> python scripts\init_db.py              # 建庫
PS> python scripts\lint_agents.py          # 應顯示「通過」
PS> mkdir $HOME\.claude\skills -Force; Copy-Item -Recurse -Force skills\* $HOME\.claude\skills\
PS> git init; git add .; git commit -m "bootstrap"
```

## 2. Discord（先只做 2 隻 Bot）
1. 建立私人伺服器 `TRADE-DESK`；開啟 `使用者設定 → 進階 → 開發者模式`。
2. 建立頻道 `#human-inbox`、`#tasks`、`#macro`、`#agent-health`、`#forge`、`#alerts`。
3. https://discord.com/developers/applications → New Application → 名稱 `TD-ROUTER`
   → Bot 頁：Reset Token（複製）、開啟 **Message Content Intent** 與 **Server Members Intent**
   → **Installation → Install Link 設成 None**（存檔）→ 回 Bot 頁才關得掉 **Public Bot**
     （順序顛倒會跳「私人應用程式不得使用預設授權連結」；存不成 None 就先 App Discovery → Disable Discovery）
   → OAuth2 URL Generator：長清單裡**只勾 scope `bot`**，權限 View Channels / Send Messages / Send Messages in Threads / Create Public Threads / Read Message History / Attach Files / Embed Links / Add Reactions / Manage Threads
   → 開啟產生的網址，邀請進伺服器。
4. 同樣流程再做一次 `TD-CEO`。
5. 右鍵伺服器圖示複製 Server ID、右鍵你的頭像複製 User ID、右鍵各頻道複製 Channel ID。

## 3. 設定
```powershell
PS> Copy-Item router\.env.example router\.env
PS> notepad router\.env      # 填 OWNER_USER_ID、GUILD_ID、DISCORD_TOKEN_ROUTER、DISCORD_TOKEN_CEO、CH_*
PS> icacls router\.env /inheritance:r /grant:r "$env:USERNAME:(R,W)"
PS> notepad agents\ceo\USER.md    # 填你的 Discord User ID
```
先只跑兩隻 Bot：把 `router\agents.yaml` 中除了 `router:` 與 `ceo:` 以外的 Agent 暫時註解掉（每行前加 `#`）。

## 4. 啟動與測試
```powershell
PS> python router\discord_router.py
```
在 Discord `#human-inbox` 輸入：
```
@TD-CEO !status
```
你應該看到：訊息出現 👀 → ⚙️ → CEO 開一個 thread 回覆 → ✅

## 5. 交棒給 CEO

CEO 一活起來，之後就由它指揮。在 `#human-inbox` 貼這段：

```
@TD-CEO 我是 Blacksheep。系統剛完成 bootstrap，Router 已上線。
請你讀 docs/08_BUILD_PLAN.md，確認目前處於哪個 Phase，並回報：
(1) 已完成什麼 (2) 下一步該做什麼 (3) 有沒有需要我先決定的事
```

接著：
- 把 `agents.yaml` 的註解拿掉，依 `docs/03_DISCORD_SETUP.md` 建完其餘 14 隻 Bot（可以邊做邊問 CEO）。
- 依 `docs/02_SETUP_GUIDE.md` 第 9 節設定工作排程器常駐。
- 之後每次推進進度，只要在 `#human-inbox` 說「@TD-CEO 開始 Phase N」。
- 需要自己動手時才 `cd dev`（見 `docs/08_BUILD_PLAN.md` 第五節）。

## 卡住了？
`docs/05_OPERATIONS.md` 的「故障排除」表；最常見的是忘了開 Message Content Intent。
