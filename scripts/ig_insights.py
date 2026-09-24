#!/usr/bin/env python3
"""
ig_insights.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 growth-fetch 排程以 exit 0 結束，
避免 Router 產生每日 BUG_REPORT 噪音。

完整實作規格（見 skills/ig-insights-collection/SKILL.md）：
  - GET /{ig-user-id}/insights?metric=reach,impressions,profile_views,follower_count&period=day
  - 逐篇 GET /{media-id}/insights?metric=reach,saved,shares,likes,comments
  - 受眾輪廓：audience_city、audience_gender_age（period=lifetime，需 ≥ 100 追蹤者）
  - 寫入 ig_insights 表 + content.metrics_24h_json / metrics_7d_json（ingest token: MARKETING）
  - token 到期前 7 天提醒 Blacksheep 與 FORGE（長期 token 60 天效期）

環境變數需求：IG_USER_ID、IG_LONG_LIVED_TOKEN、INGEST_TOKEN_MARKETING、INGEST_PORT

本檔不呼叫任何 API、不寫入資料倉。
"""
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IG-INSIGHTS-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--backfill", action="store_true")
    parser.parse_args()

    logger.warning(
        "NOT_IMPLEMENTED: ig_insights.py — 完整實作尚未部署，"
        "見 skills/ig-insights-collection/SKILL.md"
    )


if __name__ == "__main__":
    main()
