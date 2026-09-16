#!/usr/bin/env python3
"""
prefilter_1h.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 chart-1h precheck 以 exit 0 結束，
避免 Router 每小時產生 BUG_REPORT 噪音。

完整實作規格：
  - 掃描 v_latest_indicators，找到有匯合區的 symbol 後輸出候選清單
  - 無候選時輸出 "SKIP"（Router 讀到 SKIP 不觸發 CHART LLM，省額度）
  - 驗收: 無匯合區時 #analysis 完全安靜
  - 見 docs/08_BUILD_PLAN.md

本檔不呼叫任何 API、不寫入資料倉。
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PREFILTER-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        "NOT_IMPLEMENTED: prefilter_1h.py — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
    )
    # 輸出 SKIP → Router 不觸發 CHART LLM
    print("SKIP")


if __name__ == "__main__":
    main()
