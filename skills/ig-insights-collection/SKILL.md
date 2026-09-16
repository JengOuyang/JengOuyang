---
name: ig-insights-collection
description: 抓取 Instagram 帳號與貼文的 Insights 原始數據並寫入資料倉時使用
---

# ig-insights-collection

## 何時使用
每日 21:00 的數據採集，或需要補抓歷史數據時。

## 輸入 / 輸出契約
- **輸入**：Meta Graph API + `content` 表的已發佈貼文清單
- **輸出**：`ig_insights` 新增一列 / 各 content 的成效快照
- **失敗時**：API 失敗記錄錯誤碼並重試一次；token 失效 → 立即通知，不重試

## 步驟
1. `GET /{ig-user-id}/insights?metric=reach,impressions,profile_views,follower_count&period=day`。
2. 逐篇 `GET /{media-id}/insights?metric=reach,saved,shares,likes,comments`。
3. 受眾輪廓（需 ≥ 100 追蹤者）：`audience_city`、`audience_gender_age`，`period=lifetime`。
4. 經 ingest 寫入 `ig_insights` 與 `content.metrics_24h_json` / `metrics_7d_json`。
5. token 到期前 7 天提醒 Blacksheep 與 FORGE（長期 token 60 天效期）。

## 完成檢查
- [ ] 數據有寫進資料倉不只是印出來
- [ ] token 效期有監控

## 相關程式
- `scripts/ig_insights.py`

## 搬遷
複製本資料夾到 `~/.claude/skills/` 或另一專案的 `.claude/skills/`；若依賴 scripts/，一併複製並調整路徑。
