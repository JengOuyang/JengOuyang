# shared/ — 單一真相（Single Source of Truth）

**這裡的每個檔案都只有一份，永不複製貼上。** Agent 不直接讀這裡，而是讀由 `scripts/build_context.py` 生成的 `agents/<id>/.context/` 切片。

| 檔案 | 內容 | 誰在乎 |
|---|---|---|
| `CONSTITUTION.md` | 憲法：九條鐵律、人類保留權限、知識層級 | 全體，逐字一致 |
| `PROTOCOL.md` | 訊息格式、msg_type、任務生命週期、Owner 指令 | 全體 |
| `RISK_RULES.md` | A 提案要件 / G Gate 門檻 / B 倉位 / C 帳戶 / D 執行 / E 棘輪 / H 變更 | 依角色切片 |
| `METRICS_SPEC.md` | 統一績效量尺（R、勝率、Sharpe、MaxDD…） | AUDIT / LAB / REDTEAM |
| `DATA_SCHEMA.md` | 資料倉表結構與 hash chain 規格 | FEED / LEDGER / FORGE |
| `MARKETING_PLAYBOOK.md` | 品牌、內容支柱、格式、量測、合規 | CMO / CREATIVE / GROWTH |
| `universe.yaml` | 四層商品宇宙、群組、時段、流動性門檻 | RISK / CHART / FEED |
| `strategy_params.yaml` | **所有數值集中在此**，版本化，Owner 核准才能改 | RISK / EXEC / LAB |
| `context_map.yaml` | 誰能看到哪些條款（切片規則） | FORGE |
| `view_grants.yaml` | 誰能查哪些視圖（資料權限矩陣） | FORGE |
| `schemas/` | JSON Schema，程式用它驗證 Agent 的輸出 | 全體程式 |

**改了這裡的任何檔案，必須跑 `python scripts/build_context.py`**，否則 Agent 會偵測到雜湊不符而停工。
