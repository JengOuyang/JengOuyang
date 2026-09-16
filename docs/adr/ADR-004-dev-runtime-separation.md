# ADR-004：開發工作區與 Agent 運行區分離

狀態：**採納** · 日期 2026-09-09

## 背景
Claude Code 會載入 cwd 與**所有上層目錄**的 `CLAUDE.md`。若專案根目錄有 `CLAUDE.md`，它會同時進入開發者 session 與 15 個 Agent 的 session——不論寫的是開發指示還是 Agent 憲法，總有一邊會錯亂。

## 選項
| 方案 | 隔離 | 摩擦 |
|---|---|---|
| A. 根目錄放通用 `CLAUDE.md`，靠措辭兼顧兩者 | 弱，且內容必然模糊 | 低 |
| B. 開發與運行分成兩個 repo，用 build/deploy 同步 | 強 | 高（每次改動要部署） |
| C. 根目錄不放 `CLAUDE.md`；開發在 `dev/`，Agent 共同層在 `agents/CLAUDE.md` | 強 | 極低（只需 `cd dev`） |

## 決定
選 **C**。`dev/` 與 `agents/` 是兄弟目錄，唯一的共同祖先（專案根）刻意沒有 `CLAUDE.md`，兩條繼承鏈不相交。
`dev/.claude/settings.json` 設 `additionalDirectories: [".."]`，所以在 `dev/` 仍能讀寫整個 repo。

## 後果
- 開發時路徑要寫 `../engine/...`，是小小的不便。
- **必須記住：根目錄永遠不要放 `CLAUDE.md`**。`lint_agents.py` 未來可加這項檢查。
- `~/.claude/CLAUDE.md`（使用者層）仍會被全體繼承，這是 Claude Code 的行為，只能靠紀律避免（已寫入 `04_DEV_ENVIRONMENT.md` 與 `dev/NOTES.md`）。

## 何時重新考慮
若團隊變成多人開發，改採 B（獨立的 deploy 流程），因為那時「誰在哪個版本上開發」會變成真問題。
