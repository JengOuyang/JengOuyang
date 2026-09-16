#!/usr/bin/env python3
"""
lint_agents.py — 檢查 15 個 Agent 的定義是否自洽。FORGE 每月執行，Router 啟動時也會跑。

檢查項目：
  1. 每個 Agent 目錄有 CLAUDE.md / PERSONA.md / MANUAL.md / USER.md / .claude/settings.json
  2. MANUAL.md 列出的 skills 在 skills/ 下存在
  3. agents.yaml 的 agent 與 agents/ 目錄一一對應
  4. context_map.yaml 涵蓋所有 Agent；.context/ 已生成且與 shared/ 一致
  5. view_grants.yaml 的視圖都在 db/002_views.sql 定義過
  6. scheduler.yaml 的 agent 與 job 名稱都有對應
  7. PROTOCOL.md 定義的 msg_type 涵蓋各 MANUAL 使用的 msg_type
  8. Agent 的 allowed_tools 只用相對路徑 ../../ 呼叫共用腳本
  9. Skill 原子性：步驟數與檔案大小在合理範圍、有輸入/輸出契約
 10. 依賴方向：engine/ 不得 import agents/；LLM Agent 不得直接寫 data/
 11. 根目錄不得有 CLAUDE.md（否則開發 session 與 Agent 互相污染）
 12. 排程負載：任兩個 opus 間隔 ≥ 5 小時；任一 5 小時滑動窗權重 ≤ 6（最壞情況：每日×星期×幾號）
 13. 各 MANUAL 的排程行與 scheduler.yaml 一致（由 sync_manual_cron.py 生成）
 14. 每個 .claude/settings.json 的 deny 基線與 model 別名
 15. 文件宣稱的數字與檔案路徑與 repo 一致（verify_docs_claims.py）
 16. 每個程式型 job 都有對應的 script（否則它永遠不會執行）
 17. 每份 MANUAL 的「訊息收發」與 PROTOCOL.md 的 msg_type 表一致
 18. .context/ 的每個生成檔都出現在該 Agent 的 CLAUDE.md @import 清單
 19. 職責不重疊、交接兩端齊備、寫入權與 shared/OWNERSHIP.yaml 相符（verify_isolation.py）
 20. 15 份共同認知卡（MISSION）逐字一致
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
problems: list[str] = []
warnings: list[str] = []


def load(p): return yaml.safe_load((ROOT / p).read_text(encoding="utf-8"))



def run_check(script: str, *args: str) -> tuple[int, str]:
    """跑一支驗證腳本，回傳 (returncode, 給人看的訊息)。

    兩個教訓寫在這裡：
      1. Windows 的 cp950 主控台會讓子程序 print 中文/符號時崩潰。
         → 子程序環境強制 PYTHONIOENCODING=utf-8，這一端也用 utf-8 解碼。
      2. 子程序若是「崩潰」而不是「回報問題」，stdout 是空的、訊息在 stderr。
         v3.0.5 之前這裡只挑 stdout 的 ERROR 行，使用者看到的是
         「ERROR [19] 隔離驗證失敗：」後面一片空白，完全無從查起。
         → 沒有 ERROR 行時，把 stderr 的最後幾行原樣端出來。
    """
    import os
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=ROOT)
    if r.returncode == 0:
        return 0, ""
    errs = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("ERROR")]
    if errs:
        return r.returncode, "\n".join(errs)
    tail = [l for l in (r.stderr or "").splitlines() if l.strip()][-6:]
    if tail:
        return r.returncode, (f"{script} 自己崩潰了（退出碼 {r.returncode}），最後幾行：\n  "
                              + "\n  ".join(tail))
    out = [l for l in (r.stdout or "").splitlines() if l.strip()][-6:]
    return r.returncode, (f"{script} 退出碼 {r.returncode}，但沒有任何訊息"
                          + ("\n  " + "\n  ".join(out) if out else "（stdout 與 stderr 都是空的）"))


def main() -> int:
    cfg = load("router/agents.yaml")
    sched = load("router/scheduler.yaml")
    cmap = load("shared/context_map.yaml")
    grants = load("shared/view_grants.yaml")
    yaml_agents = {k for k, v in cfg["agents"].items() if v.get("kind") != "router"}
    dir_agents = {p.name for p in (ROOT / "agents").iterdir() if p.is_dir() and not p.name.startswith(".")}
    skills = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}

    # 1 & 3
    for a in sorted(yaml_agents | dir_agents):
        if a not in yaml_agents:
            problems.append(f"[3] agents/{a}/ 存在但 router/agents.yaml 沒有定義")
        if a not in dir_agents:
            problems.append(f"[3] agents.yaml 定義了 {a} 但 agents/{a}/ 不存在")
            continue
        d = ROOT / "agents" / a
        for f in ("CLAUDE.md", "PERSONA.md", "MANUAL.md", "USER.md", ".claude/settings.json"):
            if not (d / f).exists():
                problems.append(f"[1] agents/{a}/{f} 缺少")
        # 2
        manual = (d / "MANUAL.md").read_text(encoding="utf-8") if (d / "MANUAL.md").exists() else ""
        for s in re.findall(r"^- `([a-z0-9\-]+)`", manual, re.M):
            if s not in skills:
                problems.append(f"[2] {a} 的 MANUAL 引用了不存在的 skill：{s}")
        # 4
        if a not in cmap["slices"]:
            problems.append(f"[4] context_map.yaml 缺少 {a} 的切片定義")
        # 8
        for t in cfg["agents"].get(a, {}).get("allowed_tools", []):
            if "scripts/" in t and "../../" not in t:
                problems.append(f"[8] {a} 的 allowed_tools 用了非相對路徑：{t}")

    # 4b 上下文一致性
    import subprocess
    rc, msg = run_check("build_context.py", "--verify")
    if rc != 0:
        problems.append("[4] 上下文完整性驗證失敗：\n" + msg)

    # 5
    sql = (ROOT / "db" / "002_views.sql").read_text(encoding="utf-8")
    defined = set(re.findall(r"CREATE VIEW IF NOT EXISTS (\w+)", sql))
    need = set(grants["common"]) | {v for lst in grants["grants"].values() for v in lst}
    for v in sorted(need - defined):
        problems.append(f"[5] view_grants 授權了未定義的視圖：{v}")
    for a in yaml_agents:
        if a not in grants["grants"]:
            warnings.append(f"[5] {a} 沒有任何視圖授權（若不需查資料可忽略）")

    # 6
    job_names = set()
    for j in sched["jobs"]:
        if j["agent"] not in yaml_agents:
            problems.append(f"[6] scheduler job {j['name']} 指向不存在的 agent {j['agent']}")
        if j["name"] in job_names:
            problems.append(f"[6] scheduler job 名稱重複：{j['name']}")
        job_names.add(j["name"])
        a = cfg["agents"].get(j["agent"], {})
        if a.get("kind") == "program" and j["name"] not in (a.get("scripts") or {}):
            problems.append(f"[6] 程式型 agent {j['agent']} 沒有對應 job {j['name']} 的 script")

    # 7
    proto = (ROOT / "shared" / "PROTOCOL.md").read_text(encoding="utf-8")
    types = set(re.findall(r"^\| ([A-Z][A-Z_]+) \|", proto, re.M))
    for a in sorted(dir_agents):
        manual = (ROOT / "agents" / a / "MANUAL.md")
        if not manual.exists():
            continue
        # 檔名（OPTIMIZATION_CYCLE.md）與路徑不是 msg_type，先剔除
        text = re.sub(r"[A-Z][A-Z_]+\.md", "", manual.read_text(encoding="utf-8"))
        for t in set(re.findall(r"\b([A-Z]{3,}(?:_[A-Z]+)+)\b", text)):
            if t in {"SMC", "JSON", "SQL", "API", "URL", "KPI", "OK"} or "_" not in t:
                continue
            if t not in types and t not in {"RISK_RULES", "METRICS_SPEC", "DATA_SCHEMA", "MARKETING_PLAYBOOK",
                                            "TRADE_DESK", "NO_SETUP", "PROTOCOL_ERROR", "STOP_HUNT_THEN_REVERSAL",
                                            "TREND_FAILURE", "WRONG_HTF_BIAS", "EVENT_SHOCK", "EXECUTION_SLIPPAGE",
                                            "PREMATURE_ENTRY", "STOP_TOO_TIGHT", "MACRO_CONFLICT", "DATA_ISSUE",
                                            "SESSION_LIQUIDITY", "AGREE_WITH_CONCERNS", "BUILD_PLAN", "RISK_ON", "RISK_OFF", "EVENT_RISK", "LONG_ONLY",
                                            "SHORT_ONLY", "USDT_FUTURES", "MARKETING_METRICS", "POSITION_CLOSED"}:
                warnings.append(f"[7] {a} 的 MANUAL 使用了 PROTOCOL 未定義的 msg_type：{t}")

    # 9 Skill 原子性（超標只是警告——「不是所有東西都要原子性」，但要看得見）
    for sk in sorted(skills):
        f = ROOT / "skills" / sk / "SKILL.md"
        if not f.exists():
            problems.append(f"[9] skills/{sk}/SKILL.md 缺少"); continue
        txt = f.read_text(encoding="utf-8")
        steps = len(re.findall(r"^\d+\. ", txt, re.M))
        if steps > 8:
            warnings.append(f"[9] skill {sk} 有 {steps} 個步驟（建議 ≤ 8）——考慮拆成更小的技能")
        if len(txt) > 4000:
            warnings.append(f"[9] skill {sk} 有 {len(txt)} bytes（建議 ≤ 4000）——可能塞了多件事")
        if "## 輸入 / 輸出契約" not in txt:
            warnings.append(f"[9] skill {sk} 沒有「輸入 / 輸出契約」段落——無法獨立測試與替換")

    # 10 依賴方向
    for f in (ROOT / "engine").glob("*.py"):
        t = f.read_text(encoding="utf-8")
        if re.search(r"^\s*(from|import)\s+.*agents", t, re.M):
            problems.append(f"[10] engine/{f.name} 不得依賴 agents/（執行層不該知道思考層的存在）")
    for a in sorted(dir_agents):
        for t in cfg["agents"].get(a, {}).get("allowed_tools", []):
            if re.search(r"(Write|Edit)\(.*data/", t):
                problems.append(f"[10] {a} 被允許直接寫 data/——資料倉唯一寫入口是 engine/ingest_server.py")

    # 12 排程負載（Claude Pro 是 5 小時滾動窗，痛的是爆量不是總量）
    WEIGHT = {"opus": 3.0, "sonnet": 1.0, "haiku": 0.2}
    MAX_WINDOW, MIN_OPUS_GAP = 6.0, 300      # 權重上限、opus 最小間隔（分鐘）

    def _slots(job):
        """回傳 [(日別, 當日分鐘數)]；只處理固定時刻的 cron。"""
        mm, hh, dom, _mon, dow = job["cron"].split()
        if not (mm.isdigit() and hh.isdigit()):
            return []
        t = int(hh) * 60 + int(mm)
        if dow != "*":
            return [(f"週{d}", t) for d in dow.split(",")]
        if dom != "*":
            return [(f"{d}號", t) for d in dom.split(",")]
        return [("每日", t)]

    buckets: dict[str, list] = {"每日": [], **{f"週{d}": [] for d in range(7)}}
    monthly: dict[str, list] = {}
    for j in sched["jobs"]:
        if j.get("program"):
            continue
        ag = cfg["agents"].get(j["agent"], {})
        if ag.get("kind") != "llm":
            continue
        w = WEIGHT.get(j.get("model") or ag.get("model", "sonnet"), 1.0)
        # 互斥任務（precheck 決定跑哪一個）只計一次：權重歸給主任務，備援記 0
        if j.get("mutex_with"):
            w = 0.0
        for day, t in _slots(j):
            (monthly if day.endswith("號") else buckets).setdefault(day, []).append((t, j["name"], w))

    daily = buckets["每日"]
    # 每個「幾號」都可能落在任何星期幾，必須連同該星期的週報一起算（最壞情況）
    cases = [(f"週{d}", daily + buckets[f"週{d}"]) for d in range(7)]
    cases += [(f"{dom}（{wd}）", daily + buckets[wd] + jobs)
              for dom, jobs in monthly.items() for wd in (f"週{d}" for d in range(7))]
    cases.insert(0, ("每日", daily))

    for day, raw in cases:
        items = sorted(raw)
        for t0, n0, _ in items:
            win = sum(w for t, _, w in items if t0 <= t < t0 + 300)
            if win > MAX_WINDOW:
                names = [n for t, n, _ in items if t0 <= t < t0 + 300]
                problems.append(f"[12] {day} {t0//60:02d}:{t0%60:02d} 起的 5 小時窗權重 {win:.1f} > {MAX_WINDOW}："
                                f"{', '.join(names)}（R2：把其中一項移到 5 小時外）")
                break
        opus = sorted((t, n) for t, n, w in items if w >= 3.0)   # 互斥備援權重為 0，不參與間隔檢查
        for (t1, n1), (t2, n2) in zip(opus, opus[1:]):
            if t2 - t1 < MIN_OPUS_GAP:
                problems.append(f"[12] {day} 的 opus 任務間隔僅 {t2-t1} 分鐘：{n1} → {n2}（R1：需 ≥ 300 分鐘）")

    # 13 手冊的排程行必須與 scheduler.yaml 一致（排程表是單一真相，手抄一定會漂）
    sys.path.insert(0, str(ROOT / "scripts"))
    from sync_manual_cron import expected_lines  # noqa: E402
    for manual in sorted((ROOT / "agents").glob("*/MANUAL.md")):
        aid = manual.parent.name
        have = [l for l in manual.read_text(encoding="utf-8").splitlines() if l.startswith("- [CRON:")]
        want = expected_lines(aid, sched, cfg)
        if have != want:
            problems.append(f"[13] {aid}/MANUAL.md 的排程行與 scheduler.yaml 不符"
                            f"（跑 `python scripts/sync_manual_cron.py` 重新生成）")

    # 14 settings.json 的 deny 基線（唯一有寫入權的 Agent 不能是防護最弱的那一個）
    BASELINE_DENY = ["Bash(rm *)", "Read(../../router/.env)", "Bash(python -c *)",
                     "Write(../../shared/**)", "Edit(../../shared/**)",
                     "Write(.context/**)", "Edit(.context/**)"]
    for a in sorted(dir_agents):
        f = ROOT / "agents" / a / ".claude" / "settings.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text(encoding="utf-8"))
        deny = set(st.get("permissions", {}).get("deny", []))
        for d in BASELINE_DENY:
            if d not in deny:
                problems.append(f"[14] {a}/.claude/settings.json 的 deny 缺少基線項目：{d}")
        want_model = cfg["agents"].get(a, {}).get("model", "sonnet")
        if st.get("model") != want_model:
            problems.append(f"[14] {a}/.claude/settings.json 的 model={st.get('model')} 與 agents.yaml 的 {want_model} 不符")

    # 15 文件宣稱的數字與路徑（白皮書說 41 個視圖、實際 44 個這類漂移）
    rc, msg = run_check("verify_docs_claims.py")
    if rc != 0:
        problems.append("[15] 文件宣稱與實際不符：\n" + msg)

    # 16 每個 program 型 job 都要有對應 script（棘輪曾經沒有任何觸發器）
    for j in sched["jobs"]:
        ag = cfg["agents"].get(j["agent"], {})
        if ag.get("kind") == "program" and j["name"] not in (ag.get("scripts") or {}):
            problems.append(f"[16] 程式型 job {j['name']} 在 agents.yaml 沒有對應 script——它永遠不會執行")

    # 17 訊息收發段落與 PROTOCOL.md 一致（稽核曾發現 35 個沒有收件方的 msg_type）
    rc, msg = run_check("sync_manual_msgflow.py", "--verify")
    if rc != 0:
        problems.append("[17] 手冊的訊息收發與 PROTOCOL.md 不符"
                        "（跑 `python scripts/sync_manual_msgflow.py`）：\n" + msg)

    # 18 生成的切片必須真的被 @import，否則等於沒生成（OPTIMIZATION_CYCLE 曾經整份沒進任何 context）
    for a in sorted(dir_agents):
        ctx = ROOT / "agents" / a / ".context"
        cl = ROOT / "agents" / a / "CLAUDE.md"
        if not ctx.exists() or not cl.exists():
            continue
        imports = cl.read_text(encoding="utf-8")
        for f in sorted(ctx.glob("*.md")):
            if f"@.context/{f.name}" not in imports:
                problems.append(f"[18] {a}/CLAUDE.md 沒有 @import .context/{f.name}——這份切片生成了卻不會進 context")

    # 19 職責不重疊、交接兩端齊備、寫入權與 OWNERSHIP 相符
    rc, msg = run_check("verify_isolation.py")
    if rc != 0:
        problems.append("[19] 隔離驗證失敗：\n" + msg)

    # 20 共同認知卡必須逐字一致（與憲法同等級）——任何一份不同就代表 Agent 的目標認知分岐
    mission = (ROOT / "shared" / "MISSION.md").read_text(encoding="utf-8")
    for a in sorted(dir_agents):
        f = ROOT / "agents" / a / ".context" / "mission.md"
        if not f.exists():
            problems.append(f"[20] {a} 缺少共同認知卡 .context/mission.md")
        elif f.read_text(encoding="utf-8") != mission:
            problems.append(f"[20] {a} 的共同認知卡與 shared/MISSION.md 不一致")

    # 21 OS 層沙箱（L0）必須與 OWNERSHIP.yaml 同步——工具層擋不住會寫檔又會執行程式的 Agent
    rc, msg = run_check("sync_sandbox.py", "--verify")
    if rc != 0:
        problems.append("[21] 沙箱設定與 OWNERSHIP.yaml 不符：\n" + msg)

    # 22 Markdown 表格結構（v3.0 曾把一列插到表格外面，HTML 印出裸的 | 字元卻沒人發現）
    sys.path.insert(0, str(ROOT / "scripts"))
    from md_tables import orphan_table_rows  # noqa: E402
    for f in sorted(ROOT.glob("docs/*.md")) + sorted(ROOT.glob("shared/*.md")) + [ROOT / "README.md"]:
        if not f.exists():
            continue
        for ln, txt in orphan_table_rows(f.read_text(encoding="utf-8")):
            problems.append(f"[22] {f.relative_to(ROOT)} 第 {ln} 行是孤兒表格列（不屬於任何表格）：{txt[:60]}")

    # 23 排程指向的程式若尚未存在，必須在 BUILD_PLAN 裡（否則是永遠不會被建的靜默缺口）
    plan = (ROOT / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
    for aid, a in cfg["agents"].items():
        for job, cmdline in (a.get("scripts") or {}).items():
            for tok in cmdline.split():
                if not tok.endswith(".py"):
                    continue
                if (ROOT / tok).exists():
                    continue
                if Path(tok).name not in plan:
                    problems.append(f"[23] {aid} 的 job「{job}」指向 {tok}，該檔不存在"
                                    f"且 BUILD_PLAN 沒有列它——這個排程永遠不會有東西可跑")

    # 24 requirements.txt 必須涵蓋所有第三方 import
    #    （v3.0.2 發現 apscheduler / python-dotenv / Markdown 都漏了——Router 會在啟動時才炸）
    import ast as _ast
    STD = set(sys.stdlib_module_names)
    LOCAL = ({p.stem for p in (ROOT / "scripts").glob("*.py")}
             | {p.stem for p in (ROOT / "engine").glob("*.py")}
             | {"router", "engine", "scripts", "tests"})
    ALIAS = {"discord": "discord.py", "yaml": "pyyaml", "dotenv": "python-dotenv", "PIL": "pillow"}
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    seen = {}
    from td_paths import project_py_files      # 排除 .venv / site-packages / 生成物
    for f in project_py_files(ROOT):
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            problems.append(f"[24] {f.relative_to(ROOT)} 語法錯誤，無法解析"); continue
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Import):
                names = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, _ast.ImportFrom) and n.level == 0 and n.module:
                names = [n.module.split(".")[0]]
            else:
                continue
            for nm in names:
                if nm not in STD and nm not in LOCAL:
                    seen.setdefault(nm, f.relative_to(ROOT))
    for nm, where in sorted(seen.items()):
        pkg = ALIAS.get(nm, nm).lower()
        if pkg not in req and nm.lower() not in req:
            problems.append(f"[24] {where} import 了 `{nm}`，但 requirements.txt 沒有它"
                            f"——使用者照手冊安裝後仍會 ModuleNotFoundError")

    # 25 指令裡的反斜線路徑也要存在
    #    （v3.0.4：DAY0 叫使用者 `pip install -r router\requirements.txt`，那個檔在根目錄，
    #     使用者照做就會失敗。原本的檢查只認 `python scripts/x.py` 這種正斜線形式。）
    plan_txt = (ROOT / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
    # 執行時才生成的檔，不該要求它現在就存在
    RUNTIME = {"Activate.ps1", "projects.yaml", ".env", "requirements.lock"}
    # 只驗「來源」：-r 的參數、notepad 要開的檔、Copy-Item 的第一個參數
    CMD_PATH = re.compile(
        r"(?:-r|notepad)\s+([A-Za-z0-9_.\\/-]+\.(?:txt|yaml|yml|md|json|example))"
        r"|Copy-Item\s+(?:-\S+\s+)*([A-Za-z0-9_.\\/-]+\.(?:txt|yaml|yml|md|json|example))")
    for f in sorted(ROOT.glob("docs/*.md")) + [ROOT / "README.md", ROOT / "QUICKSTART.md"]:
        if not f.exists():
            continue
        for groups in set(CMD_PATH.findall(f.read_text(encoding="utf-8"))):
            m = next((g for g in groups if g), "")
            rel = m.replace("\\", "/").lstrip("./")
            if not rel or rel.startswith(("C:", "D:", "$HOME", "http")) or Path(rel).name in RUNTIME:
                continue
            if not (ROOT / rel).exists() and Path(rel).name not in plan_txt:
                problems.append(f"[25] {f.name} 的指令用到 `{m}`，但這個檔不存在"
                                f"——使用者一鍵複製就會失敗")

    # 26 會印非 ASCII 的腳本必須掛 td_console（否則 Windows cp950 主控台會讓它崩潰）
    #    判準：真的會 print，而且 print 出去的東西含非 ASCII。
    #    只有 docstring 或註解是中文（例如 td_paths.py）不算——它不印東西，不會崩潰。
    for f in sorted(ROOT.glob("scripts/*.py")):
        if f.name == "td_console.py" or "td_console" in f.read_text(encoding="utf-8"):
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        prints_non_ascii = any(
            isinstance(n, _ast.Call) and getattr(n.func, "id", "") == "print"
            and not _ast.unparse(n).isascii()
            for n in _ast.walk(tree))
        if prints_non_ascii:
            problems.append(f"[26] {f.name} 會 print 非 ASCII 但沒有 `import td_console`"
                            f"——在 Windows cp950 主控台會 UnicodeEncodeError 崩潰")

    # 27 lint 自己不得直接叫子程序跑驗證腳本（會吞掉崩潰訊息）
    #    樣式用組字串，否則這一行自己就會觸發自己
    forbidden = "subprocess" + ".run("
    body = (ROOT / "scripts" / "lint_agents.py").read_text(encoding="utf-8")
    main_body = body[body.index("def main() -> int:"):]
    # 註解與字串裡提到它不算——只看真正的呼叫（v3.0.9 的第 29 項註解就提到了它）
    main_body = "\n".join(l for l in main_body.splitlines() if not l.lstrip().startswith("#"))
    main_body = main_body.replace(f'"{forbidden}"', "").replace(f"'{forbidden}'", "")
    if forbidden in main_body:
        problems.append(f"[27] lint 的 main() 直接用了 {forbidden}——請改用 run_check()，"
                        "否則子程序崩潰時使用者只會看到空的錯誤訊息")

    # 28 文件裡教使用者打的參數，腳本必須真的收得下
    #    （v3.0.7：BUILD_PLAN 教人打 `scan_legacy.py --src X --out Y --json Z`，
    #     但 --out 與 --json 根本不存在——照做只會得到 argparse 的 error。）
    def script_flags(py: Path) -> set[str]:
        try:
            tree = _ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            return set()
        out = set()
        for n in _ast.walk(tree):
            if (isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "add_argument"):
                for arg in n.args:
                    if isinstance(arg, _ast.Constant) and str(arg.value).startswith("-"):
                        out.add(str(arg.value))
        return out

    CMD = re.compile(r"python3?\s+(scripts[/\\][\w.]+\.py)((?:\s+--?[\w-]+(?:\s+[^\s|#]+)?)*)")
    for f in sorted(ROOT.glob("docs/*.md")) + [ROOT / "README.md", ROOT / "QUICKSTART.md"]:
        if not f.exists():
            continue
        for script, tail in CMD.findall(f.read_text(encoding="utf-8")):
            py = ROOT / script.replace("\\", "/")
            if not py.exists():
                continue                       # 由第 25 項與 verify_docs_claims 負責
            have = script_flags(py)
            for flag in re.findall(r"(?<!\S)(--[\w-]+)", tail):
                if flag not in have:
                    problems.append(f"[28] {f.name} 教使用者打 `{script} {flag}`，"
                                    f"但這支程式沒有這個參數（它只收 {', '.join(sorted(have)) or '無'}）")

    # 29 任何以文字模式呼叫子程序的地方都必須指定 encoding
    #    （v3.0.9：Router 的 preflight 用 subprocess.run(text=True) 沒給 encoding，
    #     Windows cp950 解 UTF-8 中文時讀取執行緒直接 UnicodeDecodeError。
    #     最陰險的是主程式仍印「OK」——例外在別的執行緒，stdout 變成空字串。）
    from td_paths import project_py_files
    for f in project_py_files(ROOT):
        if f.name == "td_proc.py":
            continue                       # 它就是那個統一入口
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in _ast.walk(tree):
            if not (isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "run"):
                continue
            mod = getattr(getattr(n.func, "value", None), "id", "")
            if mod != "subprocess":
                continue
            kw = {k.arg for k in n.keywords}
            textish = "text" in kw or "universal_newlines" in kw
            if textish and "encoding" not in kw:
                problems.append(
                    f"[29] {f.relative_to(ROOT)}:{n.lineno} 以文字模式呼叫 subprocess"
                    f"但沒有指定 encoding——Windows cp950 會 UnicodeDecodeError。"
                    f"改用 `from td_proc import run`，或補上 encoding=\"utf-8\", errors=\"replace\"")

    # 30 Router 的三個「錯誤會被吞掉」的模式（v3.0.10 全部踩到過）
    rt = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    if "except Exception" not in rt.split("async def worker")[1].split("async def")[0]:
        problems.append("[30] worker() 沒有 except——handle() 丟一次例外就會讓該 Agent 的 worker "
                        "永久消失且不出聲，症狀是「@某個 Agent 完全沒反應」")
    if re.search(r"\[-\d+\]\}", rt):
        problems.append("[30] router 有 `[-800]` 這種寫法——那是取**一個字元**，不是最後 800 字，"
                        "錯誤訊息會被毀掉（要寫 `[-800:]`）")
    # 用 AST 找「真的呼叫」，而不是註解或 docstring 裡提到它
    calls = {_ast.unparse(n.func) for n in _ast.walk(_ast.parse(rt))
             if isinstance(n, _ast.Call)}
    if "asyncio.ensure_future" in calls:
        problems.append("[30] router 用了 asyncio.ensure_future——在 APScheduler 的執行緒裡沒有事件迴圈，"
                        "會 RuntimeError 且 coroutine 永遠不被 await。排程請直接傳 coroutine function")

    # 31 不可以往 Discord 的物件上掛屬性（v3.0.11：`msg._agent = aid`）
    #    discord.py 的 Message / User / Channel 都有 __slots__，沒有 __dict__，
    #    掛屬性會在**執行時**才 AttributeError——而且是在 handle() 的第一行，
    #    等於該 Agent 每一次被觸發都失敗。靜態看得出來，就別留到線上看。
    _rt_tree = _ast.parse(rt)
    for n in _ast.walk(_rt_tree):
        if not isinstance(n, _ast.Assign):
            continue
        for t in n.targets:
            if isinstance(t, _ast.Attribute) and getattr(t.value, "id", "") in ("msg", "message"):
                problems.append(
                    f"[31] router:{n.lineno} 往 `{t.value.id}.{t.attr}` 指派——"
                    f"discord 的 Message 有 __slots__，執行時會 AttributeError。"
                    f"要傳遞的東西請當函式參數傳（例如 react(..., aid=aid)）")

    # 32 agent 的 mention 一律走 mention_of()（v3.0.11：錯誤處理器自己炸掉）
    #    `mention` 是 on_ready 才寫進 CFG 的；Bot 沒上線、或在 on_ready 之前，
    #    `a["mention"]` 就是 KeyError。它出現在 except 區塊裡，代表「處理錯誤的程式碼
    #    自己丟出新的錯誤」，原始錯誤被覆蓋，人看到的訊息與真正的病因無關。
    _safe = set()
    for fn in _ast.walk(_rt_tree):
        if isinstance(fn, _ast.FunctionDef) and fn.name == "mention_of":
            _safe = {id(x) for x in _ast.walk(fn)}
    for n in _ast.walk(_rt_tree):
        if (isinstance(n, _ast.Subscript) and isinstance(n.ctx, _ast.Load)
                and isinstance(n.slice, _ast.Constant) and n.slice.value == "mention"
                and id(n) not in _safe):
            problems.append(
                f"[32] router:{n.lineno} 直接讀 [\"mention\"]——Bot 尚未上線時是 KeyError。"
                f"請改用 mention_of(aid)（它在 Bot 沒上線時回退成純文字）")

    # 33 Router 的任何 .reply() 都不能順手 @ 被回覆的人（v3.0.13 的無限迴圈）
    #    Discord 預設 mention_author=True，會把被回覆訊息的作者放進 mentions。
    #    Bot A 回覆 Bot B 就等於 @ 了 B；B 再回覆就 @ 了 A——兩隻以機器速度互丟。
    for n in _ast.walk(_rt_tree):
        if not (isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "reply"):
            continue
        kw = {k.arg for k in n.keywords}
        if "mention_author" not in kw and "allowed_mentions" not in kw:
            problems.append(
                f"[33] router:{n.lineno} 呼叫 .reply() 但沒有關掉「回覆自動 @ 對方」——"
                f"Bot 互相回覆就會無限觸發。請改用 human_reply()，"
                f"或補上 allowed_mentions=discord.AllowedMentions(replied_user=False)")
    if "bot.user in msg.mentions" in rt:
        problems.append("[33] router 用 `bot.user in msg.mentions` 判斷有沒有被叫到——"
                        "Discord 會把被回覆訊息的作者算進 mentions，等於「有人回覆我」＝「我被叫到」。"
                        "要判斷內容裡是否真的寫了 <@id>")

    # 11 根目錄 CLAUDE.md
    if (ROOT / "CLAUDE.md").exists():
        problems.append("[11] 根目錄有 CLAUDE.md——會同時污染開發 session 與 15 個 Agent（見 ADR-004）")

    # Router 啟動時不該因為「markdown 裡的數字過期」而拒絕上線。
    # 文件漂移要擋的地方是 commit 與 CI，不是交易系統的開機。
    if "--startup" in sys.argv:
        docs_only = [p for p in problems if p.startswith("[15]") or p.lstrip().startswith("docs")]
        if docs_only and len(docs_only) == len(problems):
            # 就地改，不要重新綁定——problems / warnings 是模組層級的變數，
            # 在函式裡指派會讓整個函式的 problems 變成區域變數，前面的 append 全部 UnboundLocalError
            warnings.extend(p.replace("ERROR", "warn ")      # 降級了就不要再印 ERROR，會嚇人
                            + "（啟動模式：降為警告，請在 dev/ 跑 verify_docs_claims.py --fix）"
                            for p in problems)
            problems.clear()

    print(f"lint: {len(dir_agents)} 個 Agent、{len(skills)} 個 skill、{len(sched['jobs'])} 個排程")
    for w in warnings:
        print("  warn ", w)
    for p in problems:
        print("  ERROR", p)
    if problems:
        print(f"\n失敗：{len(problems)} 個問題")
        return 1
    print(f"\n通過（{len(warnings)} 個警告）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
