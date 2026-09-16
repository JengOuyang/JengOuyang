#!/usr/bin/env python3
"""
feed_status.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 feed on_mention 以 exit 0 結束，
避免 Router 產生 BUG_REPORT 噪音。

完整實作規格：
  - 被 @FEED mention 時回報資料倉採集狀態摘要
  - 查詢 v_data_quality / v_latest_ohlcv，輸出 MARKET_SNAPSHOT 格式
  - 見 docs/08_BUILD_PLAN.md

本檔不呼叫任何 API、不寫入資料倉。
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FEED-STATUS-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        "NOT_IMPLEMENTED: feed_status.py — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
    )


if __name__ == "__main__":
    main()
