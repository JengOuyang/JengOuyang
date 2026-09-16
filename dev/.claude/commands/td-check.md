---
description: 跑完整的 TRADE-DESK 驗證鏈（改完東西、結束 session 之前必跑）
---

依序執行下列指令，全部在專案根目錄（`..`）。**任何一項失敗就停下來修，不要繼續。**

```bash
python ../scripts/build_context.py           # shared/ 改過就要重建切片
python ../scripts/verify_docs_claims.py --fix  # 文件裡的數字對齊 repo（CHANGELOG 不動）
python ../scripts/lint_agents.py             # Agent 定義自洽（33 項）
python ../scripts/verify_isolation.py        # 職責 / 交接 / 權限 / 沙箱規則
python -m pytest ../tests -q                 # 全部測試
python ../scripts/guard_paths.py verify      # 受保護檔案有沒有被動過
```

全部通過之後，用一段話回報：**改了哪些檔、為什麼改、哪一項驗證涵蓋了這個改動**。
如果這次改動牽涉到規格或規則（`shared/`、`docs/`），還要說明對應的文件是否在同一次改動裡更新。
