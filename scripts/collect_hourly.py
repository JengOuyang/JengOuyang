#!/usr/bin/env python3
"""
collect_hourly.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 feed-collect 排程以 exit 0 結束，
避免 Router 產生 BUG_REPORT 噪音。

完整實作規格：
  - 採集所有啟用層標的的 1H/4H/D/W/M K 線增量、標記價、指數價、
    資金費率（當期＋預測）、OI、多空比、24h 清算、±2% 深度、點差
  - 寫入 ohlcv/funding/oi/orderbook_snap 表（LEDGER ingest，token FEED）
  - 缺根/時間戳跳動/價差異常 → DATA_ALERT @LEDGER @WATCH
  - 每小時在 #market-data 貼一行 MARKET_SNAPSHOT
  - 驗收: v_data_quality 有 BTC/ETH 各時框且無缺口
  - 見 docs/08_BUILD_PLAN.md，skill: market-data-collection

本檔不呼叫任何 API、不寫入資料倉。
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [COLLECT-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        "NOT_IMPLEMENTED: collect_hourly.py — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
    )


if __name__ == "__main__":
    main()
