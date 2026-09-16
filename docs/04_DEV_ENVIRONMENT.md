# 04 — 你的開發環境（以及為什麼它不會污染 Agent）

> 這份文件回答：**「我開 Claude Code 寫程式的時候，該待在哪個目錄？這樣不會又造成認知混淆嗎？」**

## 短答

**你待在 `C:\trade_desk\dev\`，不是專案根目錄。**

```powershell
cd C:\trade_desk\dev
claude
```

這樣做，你的開發 session 與 15 個 Agent 之間是**完全互不可見**的。

## 為什麼「待在根目錄」會出事

Claude Code 啟動時，會自動載入 **cwd 以及所有上層目錄**的 `CLAUDE.md`。所以如果專案根目錄有一份 `CLAUDE.md`：

```
C:\trade_desk\CLAUDE.md          ← 假設放了「開發指示」
└── agents\chart\                ← CHART 的 cwd
```

CHART 啟動時會載入 `agents/chart/CLAUDE.md` **以及** `agents/CLAUDE.md` **以及** `C:\trade_desk\CLAUDE.md`。
於是 CHART 會讀到「提交前跑 pytest」「改完 shared 要重建切片」這種與它職責無關的指示——這正是認知混淆。反過來，如果根目錄的 `CLAUDE.md` 放的是 Agent 憲法，那你開發時就會被告知「你是 TRADE-DESK 的一名 Agent」，同樣錯亂。

## 解法：讓兩條繼承鏈不相交

```
C:\trade_desk\
├── （刻意沒有 CLAUDE.md）        ← 關鍵
│
├── dev\                          ← 你的開發 cwd
│   ├── CLAUDE.md                 「你是開發者助理」
│   ├── NOTES.md                  技術決策、環境、已知的坑
│   ├── TASKS.md                  開發待辦
│   └── .claude\settings.json     additionalDirectories: [".."]
│
├── agents\
│   ├── CLAUDE.md                 「你是 TRADE-DESK 的一名 Agent」（共同層）
│   ├── chart\CLAUDE.md           「你是 CHART」
│   ├── risk\CLAUDE.md            「你是 RISK」
│   └── …
│
└── shared\ engine\ scripts\ …    兩邊都能存取的共用資源
```

| Session | cwd | 載入的 CLAUDE.md | 載入的人設 |
|---|---|---|---|
| 你開發 | `dev\` | `dev\CLAUDE.md` | 開發者助理 |
| CHART | `agents\chart\` | `agents\chart\CLAUDE.md` + `agents\CLAUDE.md` | CHART + 憲法 |
| RISK | `agents\risk\` | `agents\risk\CLAUDE.md` + `agents\CLAUDE.md` | RISK + 憲法 |

`dev\` 不是 `agents\` 的父層，`agents\` 也不是 `dev\` 的父層，兩者只共用一個**沒有 CLAUDE.md** 的根目錄。零污染，也不需要任何額外的建置步驟。

## 你在 dev\ 還是能改整個專案

`dev\.claude\settings.json` 已設定：

```json
{ "permissions": { "additionalDirectories": [".."] } }
```

所以你可以正常編輯 `..\engine\executor.py`、`..\shared\RISK_RULES.md` 等等。只是路徑要寫 `../`——這點小小的不便，換到的是乾淨的隔離。

## ⚠️ 一個容易忽略的污染源：`~/.claude/CLAUDE.md`

Claude Code 還會載入**使用者層**的 `C:\Users\<你>\.claude\CLAUDE.md`，而這一份會被**所有** session 繼承，包括 15 個 Agent。

**不要在那裡放這個專案的開發偏好**（例如「一律用繁體中文回覆」「提交前跑 pytest」）。若你已經有內容，請確認它對 CHART、RISK 這些角色也是無害的通則。同理，`~/.claude/skills/` 裡安裝的 skill 全體可見——這是我們刻意利用的（技能共享），但別放進帶有角色假設的東西。

## 開發時不要撞到正在運行的系統

開發環境與運行環境**共用同一份程式碼與資料庫**。Router 每 5 分鐘會呼叫 `engine/risk_gate.py`、`engine/executor.py`。所以：

| 你要改什麼 | 先做什麼 |
|---|---|
| `engine/executor.py`、`engine/risk_gate.py`、`engine/ingest_server.py` | 確認 `strategy_params.yaml: mode: DEMO`，或在 `#human-inbox` 下 `!pause` |
| `shared/` 任何檔案 | 改完立刻跑 `python ..\scripts\build_context.py`，否則 Agent 會因雜湊不符停工 |
| `router/agents.yaml`、`scheduler.yaml` | 重啟 Router 才生效 |
| 其他（`backtest/`、`dashboard/`、`scripts/` 未排程的） | 直接改，不影響運行 |

**真錢模式下要做大改動**：用 git worktree 開獨立工作區，測完再合併。
```powershell
cd C:\trade_desk
git worktree add C:\trade_desk-work\feat-xxx -b feat/xxx
cd C:\trade_desk-work\feat-xxx\dev
claude
```
這樣運行中的 `C:\trade_desk` 完全不受影響。FORGE 修 bug 時走的也是這條路徑。

## 開發時測試單一 Agent

不必啟動整個 Router，直接在該 Agent 目錄呼叫：

```powershell
cd C:\trade_desk\agents\chart
claude -p "請用 PROTOCOL 格式回覆一則 NO_SETUP，理由：tradeable_direction 為 NONE" --output-format json --model sonnet
```

想互動式地跟某個 Agent 對話（例如調整它的人設）：
```powershell
cd C:\trade_desk\agents\chart
claude          # 這時你就是在「扮演 Router」跟 CHART 對話
```
這是安全的——你只是進到了 CHART 的 context，沒有污染任何東西。改完 `PERSONA.md` / `MANUAL.md` 後記得跑 `python ..\..\scripts\lint_agents.py`。

## 檢查清單

- [ ] `C:\trade_desk\` 根目錄**沒有** `CLAUDE.md`
- [ ] `dev\CLAUDE.md` 存在，且沒有任何「你是某個 Agent」的字眼
- [ ] `agents\CLAUDE.md` 存在，且沒有任何開發流程指示
- [ ] `~/.claude/CLAUDE.md` 不含這個專案的開發偏好
- [ ] `dev\.claude\settings.json` 有 `additionalDirectories: [".."]`
- [ ] 你養成習慣：開發永遠 `cd dev`
