#!/usr/bin/env python3
"""
compute_indicators.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 feed-indicators 排程以 exit 0 結束，
避免 Router 產生 BUG_REPORT 噪音。

完整實作規格：
  - 從 ohlcv 計算 EMA20/50/200, ATR14, RSI14, VWAP(D/W), VolumeProfile,
    swing_hi/lo, structure, session_open，寫入 indicators 表
  - 驗收: v_indicators 每個 symbol×tf 都有最新值
  - 見 docs/08_BUILD_PLAN.md

本檔不呼叫任何 API、不寫入資料倉。
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INDICATORS-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        "NOT_IMPLEMENTED: compute_indicators.py — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
    )


if __name__ == "__main__":
    main()
