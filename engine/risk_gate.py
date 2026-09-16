#!/usr/bin/env python3
"""
risk_gate.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 risk-account-check 排程以 exit 0 結束，
避免 Router 每 5 分鐘產生 BUG_REPORT 噪音。

完整實作規格：
  - G1–G15 Gate 檢查 + B 節倉位 + C 節帳戶熔斷
  - spec: shared/RISK_RULES.md § A,G,B,C
  - 驗收: pytest tests/test_risk_gate.py，每條規則各一個通過與拒絕案例
  - 需 REDTEAM + Blacksheep !approve（見 docs/08_BUILD_PLAN.md）

本檔不呼叫任何 API、不寫入資料倉、不下單。
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RISK-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "(no arg)"

    if arg == "--from-discord":
        # exit 3 → Router 把訊息交給 RISK LLM Agent 處理
        logger.warning(
            "NOT_IMPLEMENTED: risk_gate.py --from-discord — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md"
        )
        sys.exit(3)

    # --account-check 或其他子命令：NOT_IMPLEMENTED，正常退出避免 BUG_REPORT 噪音
    logger.warning(
        "NOT_IMPLEMENTED: risk_gate.py %s — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md",
        arg,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
