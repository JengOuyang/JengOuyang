# 06 — 建置路線圖（8 週）

> 每週一個里程碑，每個里程碑有明確驗收標準。**沒通過驗收就不要進下一週**。
>
> 這份是「時程視角」。**可執行的待辦清單與派工方式在 `08_BUILD_PLAN.md`**——那才是 CEO 取任務的地方。

| 週 | 里程碑 | 驗收標準 |
|---|---|---|
| **1** | 團隊上線 | 16 隻 Bot 在 Discord 上線；`@TD-CEO !status` 有回應；CEO 能派工給 MACRO 並收回 `TASK_DONE`；Router 由工作排程器常駐並通過重開機測試 |
| **2** | 資料基礎 | `init_db.py` 建庫成功；`collect_hourly.py` 每小時寫入 BTC/ETH 各時框；`v_data_quality` 無缺口；`#audit-log` 每日有 `AUDIT_ANCHOR`；`test_hashchain.py` 通過 |
| **3** | 會分析 | MACRO 每日 `MACRO_BRIEF` 附來源；CHART 每日 `HTF_CONTEXT` + 每小時 1H 掃描（只提案不下單）；`prefilter_1h.py` 在無候選時輸出 SKIP；REDTEAM 盲審在 15 分鐘內回覆 |
| **4** | 會下單（DEMO） | `risk_gate.py` 的 G1–G15 各有通過與拒絕的測試案例；EXEC 在 Bitget DEMO 完成一筆完整生命週期（進場 → 止損掛上 → 棘輪 → 平倉）；AUDIT 在 15 分鐘內產出 `TRADE_REVIEW` |
| **5** | 會驗證 | LAB 交出第一份 8 年 `BACKTEST_REPORT`（含 6 段 Walk-forward、±20% 擾動、Monte Carlo）；REDTEAM 能用 `--verify` 重跑出相同結果 |
| **6** | 全流程 + 門面 | DEMO 模式連跑 7 天無人工介入；Dashboard 顯示資產、持倉、15 個 Agent 狀態；WATCH 的額度預警觸發過一次 |
| **7** | 行銷上線 | IG 轉專業帳號 + 綁粉專 + Meta App 可用；CREATIVE 用 Canva 產出圖文草稿；`!publish` 成功發佈一篇；GROWTH 抓回 Insights |
| **8** | 決策點 | 累積 4 週 DEMO 數據；實盤期望值 ≥ 回測樣本外 60%；你決定是否進入真錢 20% 資金階段 |

## 進入真錢的門檻（全部必須成立）
- [ ] DEMO 連續 ≥ 4 週，交易數 ≥ 30 筆
- [ ] DEMO 期望值 ≥ 回測樣本外期望值 × 60%
- [ ] 至少一份 `BACKTEST_REPORT` 通過 acceptance，且 REDTEAM 無 `DISAGREE`
- [ ] `!flatten` 測試成功；C1–C4 熔斷各觸發測試過一次
- [ ] 對帳連續 7 天無差異
- [ ] 你已閱讀並接受 `CONSTITUTION.md` 第三節「人類保留權限」
- [ ] 真錢初期資金上限 20%，四週後再評估

## 之後（第 9 週起）
1. T2 山寨幣：先只採集資料與回測，不交易
2. T3 貴金屬 → T4 幣股，每層都走一次「回測 → DEMO 4 週 → 20% 資金」
3. Reels、電子報、付費服務（需先確認台灣法規）
4. 若 `#agent-health` 每天出現 ⏳，升級 Claude Max 5x
