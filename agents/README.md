# agents/ — 15 個 Agent 的工作目錄

每個子目錄就是一個 Agent 的 `claude -p` 工作目錄（cwd）。

```
<id>/
├── CLAUDE.md            自動載入的入口，@import 下面各檔
├── PERSONA.md           人設：我是誰、性格、決策原則、禁忌、升級路徑
├── MANUAL.md            作業手冊：職責、觸發、輸入輸出、Skills、KPI、模板
├── USER.md              Owner 資訊（你的 Discord ID、偏好）— 必填
├── .claude/settings.json 工具白名單與 deny 規則
├── .context/            ★ 生成物：由 shared/ 切出的角色規則（不進 git）
└── outbox/              要交付的檔案放這，Router 會上傳到 Discord 後清空
```

`CLAUDE.md`（本目錄的那一份）是所有 Agent 的**父層**，會被自動繼承——放全體共通的行為規範。
`dev/` 刻意不在這條繼承鏈上，所以你開發時不會載入任何 Agent 人設。

新增 Agent：見 `docs/02_SETUP_GUIDE.md` 第 6 節，或直接請 FORGE 做。
