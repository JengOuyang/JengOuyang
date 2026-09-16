---
name: skill-authoring
description: 為 Agent 新增可搬遷 skill 的規範
---

# skill-authoring

## 何時使用
為 Agent 新增可搬遷 skill 的規範。

## 輸入 / 輸出契約
- **輸入**：SKILL_REQUEST 的能力需求與驗收標準
- **輸出**：`skills/<name>/SKILL.md` + scripts + tests，並掛到對應 Agent 的 MANUAL
- **失敗時**：需求描述無法寫出輸入/輸出契約 → 代表邊界不清，先釐清再動手

## 步驟
1. 結構：skills/<name>/SKILL.md（frontmatter name/description ≤ 1024 字元）+ scripts/ + tests/ + README.md。
2. SKILL.md 段落：何時使用、步驟、輸入輸出、檢查清單、相關程式。
3. 安裝：複製到 ~/.claude/skills/<name>/ 或專案 .claude/skills/。
4. 掛載：更新 Agent MANUAL.md「使用的 Skills」與 router/agents.yaml skills[]；跑 lint。

## 完成檢查
- [ ] frontmatter 合法
- [ ] lint 通過

## 相關程式（FORGE/LAB 實作，規格在 shared/）
- （純知識型技能，無程式）

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/` 即可使用；若依賴 scripts/，一併複製並調整路徑。
