# dev/ — 你的開發工作區

**這是你（人類）開 Claude Code 的地方。** `cd C:\trade-desk\dev` 然後 `claude`。

為什麼在這裡而不是專案根目錄：`dev/` 不在 `agents/` 的繼承鏈上，所以你的開發指示不會被 15 個 Agent 載入，Agent 的人設也不會進入你的開發 session。詳見 `docs/04_DEV_ENVIRONMENT.md` 與 `docs/adr/ADR-004`。

| 檔案 | 內容 |
|---|---|
| `CLAUDE.md` | 開發者助理的指示：專案是什麼、硬規則、常用指令 |
| `NOTES.md` | 穩定的技術決策、環境、已知的坑、待確認的假設 |
| `TASKS.md` | 開發待辦（P0–P3），依 `docs/06_ROADMAP.md` 排序 |

`.claude/settings.json` 已設 `additionalDirectories: [".."]`，所以你在這裡能讀寫整個 repo。
