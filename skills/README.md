# skills/ — 可搬遷的技能包

`skills/<name>/SKILL.md` = 一個能力的標準作業程序。安裝到 `~/.claude/skills/` 後，所有 Agent 與你的其他專案都能用。

```
<name>/
├── SKILL.md      frontmatter(name, description) + 何時使用 / 步驟 / 完成檢查 / 相關程式
├── scripts/      （選用）該技能專屬的程式
└── tests/        （選用）
```

分類：
- 協作類：`discord-protocol`、`task-management`
- 資料類：`data-readonly`、`data-integrity`、`market-data-collection`
- 分析類：`smc-analysis`、`multi-timeframe-structure`、`macro-briefing`、`event-calendar`
- 風控執行：`risk-gate`、`position-sizing`、`bitget-execution`、`ratchet-management`
- 研究稽核：`backtest-walkforward`、`blind-review`、`trade-postmortem`、`performance-metrics`
- 工程：`agent-forge`、`skill-authoring`、`agent-health-monitoring`、`llm-budget`
- 行銷：`marketing-strategy`、`content-calendar`、`ig-copywriting`、`canva-content`、`chart-rendering`、`content-knowledge`、`growth-analytics`、`seo-keywords`、`audience-research`

新增 skill 的規範見 `skills/skill-authoring/SKILL.md`。
