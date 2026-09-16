# 行銷手冊（MARKETING_PLAYBOOK.md）— 個人交易分析品牌（IG 為主）

CMO、CREATIVE、GROWTH 三個 Agent 的共同規範。所有內容皆須符合第 6 節合規。

## 1. 品牌定位（CMO 每季檢視，Owner 核准）
- 一句話：「用機構級的多時框 + 總經框架，每天一張圖看懂 BTC/ETH（之後擴到黃金與美股）」。
- 受眾 Persona（初版，GROWTH 每月以真實數據修正）：
  - P1 進階散戶：看得懂 K 線，想要有紀律的框架與每日方向。
  - P2 剛入門者：想學 SMC／風控，被術語嚇到。
  - P3 同業／KOL：看重透明績效與方法論，可能合作。
- 差異化：績效透明（AUDIT 驗證後才發）、風控先行、用 AI 團隊產製但由人核准。

## 2. 內容支柱與頻率
| 支柱 | 內容 | 頻率 | 來源 |
|---|---|---|---|
| 每日總經一圖 | regime、bias、今日事件 | 每日 1 | MACRO_BRIEF |
| BTC/ETH 盤面一圖 | HTF 結構、關鍵區、方向（不給進場價） | 每日 1（可與上合併為輪播） | HTF_CONTEXT |
| 週回顧 | 本週市場、我們的判斷對錯（誠實） | 週日 | AUDIT 週報 |
| 教育貼文 | SMC／風控／凱利／棘輪 一個概念一張圖 | 週 2 | skills 知識庫 |
| 績效透明 | 月度 R、勝率、MaxDD（AUDIT 產生） | 月 1 | METRICS |
| Reels（第二階段） | 60 秒盤面講解 | 週 1 | CREATIVE 腳本 |

## 3. 格式規範
- 圖：1080×1350 直式；品牌色與字體固定（Canva 品牌模板 `TD-Daily-Macro`、`TD-Daily-Chart`、`TD-Edu`、`TD-Weekly`）；每張圖左上品牌標、右下日期、底部固定「非投資建議」。
- 文案：繁體中文；前 125 字必須是 hook（結論或反直覺數字）；分段短句；結尾 CTA（儲存／分享／留言問題）；hashtag 10–15 個（大 3、中 7、小 5）；alt text 一句。
- 不出現：具體進場價、「保證」「穩賺」、未經 AUDIT 的績效、他人帳號截圖。

## 4. 發佈流程
CREATIVE 產出 → `marketing/queue/<date>/<content_id>/{image.jpg, caption.txt, alt.txt, meta.json}` → 在 `#marketing-review` 貼預覽（圖 + 文案）並發 `PUBLISH_REQUEST` → Owner `!publish <content_id>` → `scripts/publisher.py`：上傳圖到公開 URL（GitHub Pages / Cloudflare R2）→ `POST /{ig-user-id}/media`（image_url, caption）→ `POST /{ig-user-id}/media_publish` → 寫 `content` 表 → `PUBLISHED`。
Owner `!reject` 則退回 CREATIVE 修改。每日最多 2 篇。

## 5. 量測（GROWTH，統一由 engine/marketing_metrics.py 計算）
reach、impressions、engagement_rate、save_rate、share_rate、follower_growth、profile_visits、link_ctr、best_posting_hour、audience（城市／年齡／性別分布）、hashtag 表現、競品對照。
週報固定段落：本週數字 vs 上週、最佳／最差貼文與原因假設、A/B 實驗結果、下週建議（給 CMO）。

## 6. 合規（不可協商）
- 每篇加聲明：「本內容僅為市場觀察與教育分享，非投資建議；交易有風險。」
- 不提供個別化投資建議、不收費代操、不引導至未揭露風險的付費服務。
- 績效數字只能來自 AUDIT 的 METRICS_SPEC 報表，並標註期間、是否含模擬盤。
- 引用資料須附來源；不使用未授權圖片。
- 若 Owner 日後推出付費服務，須先由 CEO 提案並由 Owner 確認當地法規（台灣證券投資顧問相關規範）後才可行銷。
