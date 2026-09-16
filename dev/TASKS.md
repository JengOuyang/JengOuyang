# 開發臨時筆記（TASKS.md）

> **建置待辦的唯一真相是 `../docs/08_BUILD_PLAN.md`。** CEO 從那裡取任務派給 FORGE，FORGE 完成後在那裡打勾。
> 這份檔案只放「你自己在 `dev/` 動手時」的臨時筆記，避免兩份待辦分岔。

## 我現在自己在做什麼
- [ ] （空）

## 動手前的檢查
- [ ] 已跟 CEO 說過（`!pause` 或在 `#human-inbox` 告知），避免撞到運行中的排程
- [ ] 確認 `strategy_params.yaml: mode: DEMO`（若要改 engine/）
- [ ] 若是大改動，用 git worktree 開獨立工作區

## 做完之後
- [ ] `python ../scripts/build_context.py`（若改過 `../shared/`）
- [ ] `python ../scripts/lint_agents.py`
- [ ] `python -m pytest ../tests -q`
- [ ] 在 `#human-inbox` 告訴 CEO 做了什麼，請它叫 FORGE 補測試與文件、並在 BUILD_PLAN 打勾

## 臨時想法（想到就記，之後請 CEO 立項）
-
