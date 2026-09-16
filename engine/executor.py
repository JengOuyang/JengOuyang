#!/usr/bin/env python3
"""
executor.py — NOT_IMPLEMENTED stub

本檔是佔位符，目的是讓 exec-ratchet / exec-reconcile 排程以 exit 0 結束，
避免 Router 每 5 分鐘產生 BUG_REPORT 噪音。

完整實作規格：docs/08_BUILD_PLAN.md（需 REDTEAM + Blacksheep !approve）。
本檔不呼叫任何 API、不寫入資料倉、不下單。
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EXEC-STUB] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

IMPLEMENTED = set()  # 尚無任何子命令實作


def main() -> None:
    subcommand = sys.argv[1] if len(sys.argv) > 1 else "(no subcommand)"
    if subcommand in IMPLEMENTED:
        # 未來實作後在此分派
        raise NotImplementedError(subcommand)
    logger.warning(
        "NOT_IMPLEMENTED: executor.py %s — 完整實作尚未部署，見 docs/08_BUILD_PLAN.md",
        subcommand,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
