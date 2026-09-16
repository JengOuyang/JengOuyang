#!/usr/bin/env python3
"""
refresh_universe.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 feed-universe 排程以 exit 0 結束，
避免 Router 產生 BUG_REPORT 噪音。

完整實作規格：
  - 依 shared/universe.yaml 的規則重算四層商品宇宙（T1/T2/T3/T4）
  - CoinGecko 市值前 20 → 排除穩定幣/包裝幣/T1 → 檢查 Bitget 有永續且上市 ≥ 3 年
  - 寫入 universe 表，發 UNIVERSE_UPDATE @CEO @RISK @CHART
  - 驗收: v_universe 的分層與 universe.yaml 門檻一致，T1 仍含 BTC/ETH
  - 見 docs/08_BUILD_PLAN.md

本檔不呼叫任何 API、不寫入資料倉。
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [UNIVERSE-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        "NOT_IMPLEMENTED: refresh_universe.py — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
    )


if __name__ == "__main__":
    main()
