# 11 — 既有專案可複用資產（索引）

> 由 `python scripts/scan_legacy.py --all` 生成。每個專案的細表在 `docs/legacy/<id>.md`。

## 專案

| 代號 | 名稱 | 狀態 | 信任度 | 檔案數 | 細表 |
|---|---|---|---|---|---|
| `BS_Crypto` | 量化交易主專案 | production | high | 3030 | [細表](legacy/BS_Crypto.md) |
| `Crypto_Analysis_Agent` | 戰情室與行動端 | production | medium | 623 | [細表](legacy/Crypto_Analysis_Agent.md) |

## 能力對照（同一種能力有多個候選時，CEO 只能選一個來源）

**選擇規則**：先看信任度（production/high 優先），同級再看「已驗證的事實」是否涵蓋這個能力，最後才看行數。**不要合併兩個專案的同一種能力**——那會同時繼承兩邊的假設。

| 能力 | 候選（專案：檔數／最大檔行數） | 建議來源 | 你的決定 |
|---|---|---|---|
| backtest-walkforward | `BS_Crypto`：72 檔／19534 行（high）；`Crypto_Analysis_Agent`：35 檔／19534 行（medium） | `BS_Crypto` | |
| data-integrity | `BS_Crypto`：91 檔／44792 行（high）；`Crypto_Analysis_Agent`：9 檔／904 行（medium） | `BS_Crypto` | |
| exchange-order-placement | `BS_Crypto`：14 檔／13284 行（high） | `BS_Crypto` | |
| exchange-position-guard | `BS_Crypto`：96 檔／14702 行（high）；`Crypto_Analysis_Agent`：63 檔／2572 行（medium） | `BS_Crypto` | |
| exchange-reconciliation | `BS_Crypto`：25 檔／13284 行（high） | `BS_Crypto` | |
| macro-briefing | `BS_Crypto`：42 檔／9926 行（high） | `BS_Crypto` | |
| market-data-collection | `BS_Crypto`：154 檔／13284 行（high）；`Crypto_Analysis_Agent`：47 檔／3660 行（medium） | `BS_Crypto` | |
| pattern-analysis | `BS_Crypto`：133 檔／13284 行（high）；`Crypto_Analysis_Agent`：10 檔／3660 行（medium） | `BS_Crypto` | |
| ratchet-management | `BS_Crypto`：26 檔／32856 行（high） | `BS_Crypto` | |
| smc-analysis | `BS_Crypto`：836 檔／13284 行（high）；`Crypto_Analysis_Agent`：75 檔／3660 行（medium） | `BS_Crypto` | |
| war-room-dashboard | `BS_Crypto`：32 檔／13284 行（high）；`Crypto_Analysis_Agent`：2 檔／346 行（medium） | `BS_Crypto` | |

## 給 CEO 的派工規則

1. 只派 **決定欄為 PORT** 的項目；`REF` 只允許讀來當參考，不得複製進 repo。
2. 一次一個能力，`legacy_paths[]` 逐檔列出——FORGE 只能讀被指派的檔。
3. 指定 `legacy-port` skill；驗收必須附 `verify_delivery.py` 的輸出。
4. 同一能力有多個候選時，在 `TASK_ASSIGN` 註明「為什麼選這個來源、放棄哪些」，寫進建置日報。
5. **移植「坑」比移植程式重要**：每個專案的「踩過的坑」必須變成新程式裡的測試案例，否則你會用新程式再踩一次。
