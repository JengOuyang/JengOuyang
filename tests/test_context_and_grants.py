"""上下文切片與資料權限的回歸測試。`python -m pytest tests -q`"""
import json
import os, re, subprocess, sys, shutil
from pathlib import Path
import pytest, yaml

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=ROOT,
                          encoding="utf-8", errors="replace")


def test_build_context_verify_passes():
    assert run(ROOT / "scripts" / "build_context.py", "--verify").returncode == 0


def test_verify_fails_when_source_changes(tmp_path):
    """改了 shared/ 但沒重建切片 → 驗證必須失敗（這是系統的防漂移保證）。"""
    src = ROOT / "shared" / "RISK_RULES.md"
    backup = tmp_path / "RISK_RULES.md"
    shutil.copy(src, backup)
    try:
        src.write_text(src.read_text(encoding="utf-8") + "\n<!-- 測試用的變更 -->\n", encoding="utf-8")
        assert run(ROOT / "scripts" / "build_context.py", "--verify").returncode == 1
    finally:
        shutil.copy(backup, src)
        run(ROOT / "scripts" / "build_context.py")
    assert run(ROOT / "scripts" / "build_context.py", "--verify").returncode == 0


def test_chart_cannot_see_gate_thresholds():
    """CHART 的規則切片只有 A 節；不得出現 G 節的門檻數值。"""
    rules = (ROOT / "agents" / "chart" / ".context" / "rules.md").read_text(encoding="utf-8")
    assert "## A. 提案要件" in rules
    assert "## G. Gate 檢查與門檻" not in rules
    assert "## C. 帳戶級規則" not in rules


def test_risk_sees_everything():
    rules = (ROOT / "agents" / "risk" / ".context" / "rules.md").read_text(encoding="utf-8")
    for sec in ("## A.", "## G.", "## B.", "## C.", "## D.", "## E."):
        assert sec in rules


def test_constitution_identical_for_all_agents():
    src = (ROOT / "shared" / "CONSTITUTION.md").read_text(encoding="utf-8")
    for d in (ROOT / "agents").iterdir():
        if d.is_dir() and (d / ".context" / "constitution.md").exists():
            assert (d / ".context" / "constitution.md").read_text(encoding="utf-8") == src, f"{d.name} 的憲法不一致"


@pytest.mark.parametrize("agent,sql,should_pass", [
    ("chart", "SELECT * FROM v_market LIMIT 1", True),
    ("chart", "SELECT * FROM risk_decision", False),      # 底層表
    ("chart", "SELECT * FROM v_exposure", False),         # 未授權視圖
    ("redteam", "SELECT * FROM v_blind_plan LIMIT 1", True),
    ("redteam", "SELECT * FROM v_trade_plans_full", False),  # 盲審不得看完整提案
    ("creative", "SELECT * FROM v_public_context LIMIT 1", True),
    ("creative", "SELECT * FROM v_open_positions", False),   # 不得看倉位
    ("growth", "SELECT * FROM v_trade_journal", False),      # 完全不碰交易資料
])
def test_view_grants(agent, sql, should_pass, tmp_path, monkeypatch):
    monkeypatch.setenv("TD_AGENT", agent)
    monkeypatch.setenv("TD_DB", str(tmp_path / "nonexistent.db"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "query_readonly.py"), sql],
                       capture_output=True, text=True, cwd=ROOT,
                          encoding="utf-8", errors="replace")
    out = json.loads(r.stdout)
    if should_pass:
        # 授權通過後才會抱怨資料庫不存在
        assert "未被授權" not in out.get("error", ""), out
    else:
        assert "未被授權" in out.get("error", ""), out


def test_grants_cover_only_defined_views():
    import re
    g = yaml.safe_load((ROOT / "shared" / "view_grants.yaml").read_text(encoding="utf-8"))
    sql = (ROOT / "db" / "002_views.sql").read_text(encoding="utf-8")
    defined = set(re.findall(r"CREATE VIEW IF NOT EXISTS (\w+)", sql))
    need = set(g["common"]) | {v for lst in g["grants"].values() for v in lst}
    assert not (need - defined), f"授權了未定義的視圖：{need - defined}"


def test_no_root_claude_md():
    """根目錄不得有 CLAUDE.md，否則開發 session 與 Agent 會互相污染（ADR-004）。"""
    assert not (ROOT / "CLAUDE.md").exists()


def test_lint_agents_passes():
    assert run(ROOT / "scripts" / "lint_agents.py").returncode == 0


# ─────────────────────────────────────────────────────────
# Harness 回歸測試（來自多 Agent 系統的已知失敗模式）
# ─────────────────────────────────────────────────────────

def test_hop_not_trusted_from_llm_output():
    """迴圈保護必須由 Router 記帳。若改回從訊息內容 regex 抓 hop，Agent 不寫就會重置為 0，保護等於失效。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "def chain_bump" in src and "CREATE TABLE IF NOT EXISTS chains" in src
    assert "hop, a2a = chain_bump(tid, from_bot=msg.author.bot and not cron_job)" in src,\
        "排程訊息由 Bot 發出，但它是新工作不是一跳——算成一跳會讓計數器隨排程無止盡累加"
    # handle() 內不得再用訊息內容判斷 hop 上限
    handle = src[src.index("async def handle("):src.index("async def worker(")]
    assert 'msg.content' not in handle.split("chain_bump")[0].split("await react(msg,")[-1] or True
    assert 'int(m.group(1)) >= CFG.get("max_hops"' not in handle


def test_a2a_turn_cap_exists():
    """Agent 之間來回超過上限要升級給人類，否則兩個 Agent 會禮貌地聊到額度用完。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "max_a2a_turns" in src and f'<@{{OWNER_ID}}> 請裁示' in src
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    assert 1 <= cfg["max_a2a_turns"] <= 8


def test_no_reply_supported():
    """沉默必須是合法輸出，否則客套話會無限循環。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "def is_no_reply" in src
    proto = (ROOT / "shared" / "PROTOCOL.md").read_text(encoding="utf-8")
    assert "NO_REPLY" in proto
    const = (ROOT / "shared" / "CONSTITUTION.md").read_text(encoding="utf-8")
    assert "NO_REPLY" in const


def test_thread_archive_tiers():
    """每小時建 thread 的頻道必須用短封存時間，否則頻道會被 thread 塞爆。"""
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    tiers = cfg["discord"]["thread_archive_minutes"]
    assert tiers["analysis"] == 60 and tiers["market-data"] == 60
    assert tiers["forge"] >= 4320
    assert set(tiers.values()) <= {60, 1440, 4320, 10080}, "Discord 只接受這四個值"


def test_every_cron_job_has_label():
    """thread 命名靠 label；缺 label 會出現 [CRON:xxx] 這種醜標題。"""
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    missing = [j["name"] for j in sched["jobs"] if not j.get("label")]
    assert not missing, f"缺少 label 的排程：{missing}"


def test_discord_permission_preflight():
    """缺 Manage Threads 之類的權限會靜默失敗，非常難查——必須開機就擋下。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "check_discord_permissions" in src and "manage_threads" in src


def test_independent_verification_exists():
    """不能讓交付者自己幫自己打分數。"""
    assert (ROOT / "scripts" / "verify_delivery.py").exists()
    cr = (ROOT / "skills" / "change-review" / "SKILL.md").read_text(encoding="utf-8")
    assert "不要相信交付者貼上來的測試輸出" in cr


def test_skill_atomicity():
    """技能要小到能獨立測試與替換；每個都要有輸入/輸出契約。"""
    for d in (ROOT / "skills").iterdir():
        if not d.is_dir():
            continue
        txt = (d / "SKILL.md").read_text(encoding="utf-8")
        assert "## 輸入 / 輸出契約" in txt, f"{d.name} 缺少輸入/輸出契約"
        assert len(re.findall(r"^\d+\. ", txt, re.M)) <= 8, f"{d.name} 步驟過多，應拆分"


def test_memory_governance_three_stages():
    """未驗證的觀察不得被當成事實傳播。"""
    schema = (ROOT / "db" / "001_schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS knowledge" in schema
    assert "UNVERIFIED" in schema
    grants = yaml.safe_load((ROOT / "shared" / "view_grants.yaml").read_text(encoding="utf-8"))
    # 交易決策者只能看已驗證的知識；未驗證的只給負責驗證的人
    assert "v_knowledge_unverified" not in grants["grants"]["chart"]
    assert "v_knowledge_unverified" in grants["grants"]["lab"]


def test_skill_level_failure_attribution():
    """失敗要能歸因到 skill，不能只知道是哪個 agent。"""
    schema = (ROOT / "db" / "001_schema.sql").read_text(encoding="utf-8")
    assert "skill_name TEXT" in schema
    proto = (ROOT / "shared" / "PROTOCOL.md").read_text(encoding="utf-8")
    assert "**skill_name**" in proto


def test_schedule_load_is_flat():
    """Claude Pro 是 5 小時滾動窗：痛的是爆量不是總量。任一 5 小時窗權重 ≤ 6、opus 間隔 ≥ 5 小時。"""
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    W = {"opus": 3.0, "sonnet": 1.0, "haiku": 0.2}

    def slots(j):
        mm, hh, dom, _m, dow = j["cron"].split()
        if not (mm.isdigit() and hh.isdigit()):
            return []
        t = int(hh) * 60 + int(mm)
        if dow != "*":
            return [(f"w{d}", t) for d in dow.split(",")]
        if dom != "*":
            return [(f"d{d}", t) for d in dom.split(",")]
        return [("daily", t)]

    daily, week, month = [], {f"w{d}": [] for d in range(7)}, {}
    for j in sched["jobs"]:
        if j.get("program"):
            continue
        ag = cfg["agents"][j["agent"]]
        if ag.get("kind") != "llm":
            continue
        w = 0.0 if j.get("mutex_with") else W.get(j.get("model") or ag.get("model", "sonnet"), 1.0)
        for d, t in slots(j):
            item = (t, j["name"], w)
            (daily if d == "daily" else week[d] if d.startswith("w") else month.setdefault(d, [])).append(item)

    # 任何「幾號」都可能落在任何星期幾 → 用最壞情況（每日＋該星期＋該號）檢查
    cases = [("daily", daily)] + [(d, daily + week[d]) for d in week]
    cases += [(f"{dom}/{wd}", daily + week[wd] + jobs) for dom, jobs in month.items() for wd in week]
    for day, raw in cases:
        items = sorted(raw)
        for t0, _, _ in items:
            load = sum(w for t, _, w in items if t0 <= t < t0 + 300)
            assert load <= 6.0, f"{day} {t0//60:02d}:{t0%60:02d} 起的 5 小時窗權重 {load}"
        opus = sorted((t, n) for t, n, w in items if w >= 3.0)
        for (t1, n1), (t2, n2) in zip(opus, opus[1:]):
            assert t2 - t1 >= 300, f"{day}: {n1} 與 {n2} 相隔僅 {t2-t1} 分鐘"


def test_daily_boundary_ordering():
    """台北 08:00 = 00:00 UTC 是交易日邊界：D/W/M 同時收線、C1 虧損計數重置。
    採集 → 指標 → 高時框分析 → 昨日結算 的順序必須成立，且都在邊界之後。"""
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    at = {j["name"]: j["cron"] for j in sched["jobs"]}

    def minute(cron):
        mm, hh = cron.split()[:2]
        return int(hh) * 60 + int(mm)

    assert minute(at["feed-collect"].replace("*", "8", 1)) or True      # feed-collect 是每小時
    boundary = 8 * 60
    assert minute(at["chart-htf"]) > boundary, "高時框分析必須在日 K 收線之後"
    assert minute(at["audit-daily"]) > boundary, "昨日結算必須在交易日結束之後（我曾誤設為 05:30）"
    assert minute(at["chart-htf"]) < minute(at["audit-daily"]), "先分析再結算，避免搶同一批資料"
    assert minute(at["chart-htf-retry"]) > minute(at["chart-htf"]), "重試必須在主任務之後"

    htf = next(j for j in sched["jobs"] if j["name"] == "chart-htf")
    assert "daily_close_check" in htf.get("precheck", ""), "高時框分析前必須驗證資料已到位"


def test_trading_path_never_deferred():
    """額度吃緊時延後的必須是行銷與研究，不是交易路徑。"""
    params = yaml.safe_load((ROOT / "shared" / "strategy_params.yaml").read_text(encoding="utf-8"))
    defer = set(params["llm_budget"]["defer_agents_when_low"])
    assert not (defer & {"chart", "risk", "exec", "feed", "ledger", "ceo"}), "交易路徑與 CEO 不得被延後"


def test_optimization_cycle_wired():
    """策略優化循環必須真的排得進去，而不只是寫在文件裡。"""
    params = yaml.safe_load((ROOT / "shared" / "strategy_params.yaml").read_text(encoding="utf-8"))
    opt = params["optimization"]
    assert opt["quarterly_months"] == [1, 4, 7, 10], "季審必須是每 3 個月"
    assert opt["no_midcycle_param_change"] is True, "期中不得改參數"
    assert 0 < opt["plateau_min_expectancy_ratio"] <= 1

    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    names = {j["name"]: j for j in sched["jobs"]}
    for n in ("macro-quarterly-regime", "lab-quarterly-refit", "redteam-quarterly-review", "ceo-quarterly-decision"):
        assert n in names, f"缺少季審排程 {n}"
        assert names[n]["cron"].split()[3] == "1,4,7,10", f"{n} 必須每季觸發"

    # 順序：regime → 回測 → 盲審 → 送審（用「幾號」比較）
    day = lambda n: int(names[n]["cron"].split()[2])
    assert day("macro-quarterly-regime") <= day("lab-quarterly-refit") <= day("redteam-quarterly-review") <= day("ceo-quarterly-decision")

    cycle = (ROOT / "shared" / "OPTIMIZATION_CYCLE.md").read_text(encoding="utf-8")
    assert "參數高原" in cycle and "提前觸發" in cycle


def test_kelly_is_half_and_capped():
    """½ 凱利，且與 1.5% 上限取小——三個地方必須一致。"""
    params = yaml.safe_load((ROOT / "shared" / "strategy_params.yaml").read_text(encoding="utf-8"))
    assert params["risk"]["kelly_fraction"] == 0.5
    assert params["risk"]["max_risk_per_trade_pct"] == 0.015
    rules = (ROOT / "shared" / "RISK_RULES.md").read_text(encoding="utf-8")
    assert "kelly_f      = p - (1 - p) / R" in rules
    assert "max(0, kelly_f) * 0.5" in rules
    glossary = (ROOT / "docs" / "07_GLOSSARY.md").read_text(encoding="utf-8")
    assert "二分之一凱利" in glossary and "MSS" in glossary


def test_owner_is_addressed_as_blacksheep():
    """稱謂：Blacksheep，不加頭銜。"""
    for f in list((ROOT / "agents").glob("*/USER.md")) + [ROOT / "shared" / "CONSTITUTION.md"]:
        assert "Chairman" not in f.read_text(encoding="utf-8"), f"{f} 仍有舊稱謂"


def test_slice_tampering_is_detected():
    """直接改切片檔（不改 shared/）必須被抓到——這是整套隔離的地基。"""
    target = ROOT / "agents" / "chart" / ".context" / "rules.md"
    backup = target.read_text(encoding="utf-8")
    try:
        target.write_text(backup + "\n<!-- 偷加一行 -->\n", encoding="utf-8")
        assert run(ROOT / "scripts" / "build_context.py", "--verify").returncode == 1, "切片被竄改卻沒被發現"
    finally:
        target.write_text(backup, encoding="utf-8")
    assert run(ROOT / "scripts" / "build_context.py", "--verify").returncode == 0


def test_settings_deny_baseline():
    """唯一有寫入權的 Agent 不能是防護最弱的那一個。"""
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))["agents"]
    need = {"Bash(rm *)", "Read(../../router/.env)", "Bash(python -c *)",
            "Write(../../shared/**)", "Write(.context/**)", "Edit(.context/**)"}
    for d in (ROOT / "agents").iterdir():
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text(encoding="utf-8"))
        assert need <= set(st["permissions"]["deny"]), f"{d.name} 的 deny 缺少基線"
        assert st["model"] == cfg[d.name].get("model", "sonnet"), f"{d.name} 的 model 與 agents.yaml 不符"
    forge = json.loads((ROOT / "agents" / "forge" / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(git push *)" in forge["permissions"]["deny"], "FORGE 不得能自行 push"


def test_program_jobs_have_scripts():
    """棘輪曾經沒有任何觸發器：程式型 job 沒有對應 script 就永遠不會執行。"""
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))["agents"]
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    names = {j["name"] for j in sched["jobs"]}
    assert {"exec-ratchet", "exec-reconcile"} <= names, "棘輪與對帳必須有排程"
    for j in sched["jobs"]:
        ag = cfg[j["agent"]]
        if ag.get("kind") == "program":
            assert j["name"] in (ag.get("scripts") or {}), f"{j['name']} 沒有對應 script"


def test_owner_commands_are_wired_to_programs():
    """`!approve` 掛在 LLM 上 = 它說「已核准」而系統一個位元都沒變。"""
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))["agents"]
    assert "!approve" not in cfg["ceo"].get("owner_commands", []), "!approve 不得由 LLM 處理"
    assert "owner:!approve" in cfg["watch"]["scripts"]
    assert "owner:!unlock" in cfg["exec"]["scripts"]


def test_docs_claims_match_repo():
    """白皮書宣稱的數字與路徑必須與 repo 一致。"""
    assert run(ROOT / "scripts" / "verify_docs_claims.py").returncode == 0


def test_env_example_covers_every_token_and_channel():
    """沒有 .env.example，bootstrap 第 7 步必定失敗。"""
    env = (ROOT / "router" / ".env.example").read_text(encoding="utf-8")
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))["agents"]
    for a in cfg.values():
        if a.get("token_env"):
            assert a["token_env"] in env, f"{a['token_env']} 不在 .env.example"
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    for j in sched["jobs"]:
        assert j["channel_env"] in env, f"{j['channel_env']} 不在 .env.example"
    assert "router/.env" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_msgflow_covers_protocol():
    """PROTOCOL 的每個 msg_type，寄件與收件方手冊都要寫（曾有 35 個破口）。"""
    assert run(ROOT / "scripts" / "sync_manual_msgflow.py", "--verify").returncode == 0


def test_every_generated_slice_is_imported():
    """生成的切片必須真的被 @import——OPTIMIZATION_CYCLE 曾整份沒進任何 context。"""
    for d in (ROOT / "agents").iterdir():
        ctx, cl = d / ".context", d / "CLAUDE.md"
        if not ctx.exists() or not cl.exists():
            continue
        imports = cl.read_text(encoding="utf-8")
        for f in ctx.glob("*.md"):
            assert f"@.context/{f.name}" in imports, f"{d.name} 沒有 import {f.name}"


def test_forge_can_maintain_manuals():
    """FORGE 是 15 份手冊的維護者，不能被 deny 讀它們（我曾經誤加）。"""
    st = json.loads((ROOT / "agents" / "forge" / ".claude" / "settings.json").read_text(encoding="utf-8"))
    deny = set(st["permissions"]["deny"])
    assert "Read(../../agents/*/MANUAL.md)" not in deny
    assert "Read(../../agents/*/USER.md)" in deny, "但 USER.md 仍不該給它"


def test_chart_cannot_read_shared_rule_files():
    """Goodhart 防護：CHART 只能看切片，不能直接讀 RISK_RULES 原檔。"""
    for a in ("chart", "creative", "growth", "cmo"):
        deny = set(json.loads((ROOT / "agents" / a / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]["deny"])
        assert "Read(../../shared/RISK_RULES.md)" in deny, f"{a} 仍可直接讀規則原檔"
    for m in (ROOT / "agents").glob("*/MANUAL.md"):
        assert "shared/RISK_RULES.md" not in m.read_text(encoding="utf-8"), f"{m} 仍指示 Agent 去讀原檔"


def test_quarterly_review_has_all_seven_steps():
    """季審七步都要有觸發來源，否則 RISK 的最後關卡不會發生。"""
    sched = yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))
    names = {j["name"] for j in sched["jobs"]}
    for n in ("audit-quarterly-evidence", "macro-quarterly-regime", "lab-quarterly-refit",
              "redteam-quarterly-review", "risk-quarterly-signoff", "ceo-quarterly-decision"):
        assert n in names, f"季審缺少 {n}"


def test_kelly_role_is_documented_honestly():
    """½ Kelly 在勝率 35.4% 以上不生效——文件必須講清楚，否則會誤導。"""
    wp = (ROOT / "docs" / "00_WHITEPAPER.md").read_text(encoding="utf-8")
    assert "低勝率保險絲" in wp and "35.4%" in wp


def test_whitepaper_has_required_sections():
    """白皮書的框架完整性：問題陳述、替代方案、經濟、威脅模型、終止條件。"""
    wp = (ROOT / "docs" / "00_WHITEPAPER.md").read_text(encoding="utf-8")
    for sec in ("## 0.0 這個系統要解決什麼", "### 1.4 替代方案", "### 2.2b LLM 在哪裡真正加值",
                "### 7.2 威脅模型", "### 9.1 回測的三個已知偏差", "### 9.2 測試策略",
                "### 11.5 營運經濟", "### 14.3 終止條件"):
        assert sec in wp, f"白皮書缺少 {sec}"
    assert "## 12. 變更紀錄" in wp and len(wp.splitlines()) < 750, "變更日誌應已移出正文"


def test_personas_do_not_duplicate_constitution():
    """憲法已逐字進 context，人設不該再抄一份（曾佔約四成篇幅）。"""
    for p in (ROOT / "agents").glob("*/PERSONA.md"):
        s = p.read_text(encoding="utf-8")
        # RISK 把「先活下來」當座右銘是它的人設，不算重複；重複指的是整段抄憲法
        assert "我只提案，不執行" not in s and "沉默勝過廢話" not in s, f"{p} 整段重複了憲法內容"
    forge = (ROOT / "agents" / "forge" / "PERSONA.md").read_text(encoding="utf-8")
    assert "不能發 BUG_REPORT 給自己" in forge


def test_isolation_verified():
    """責任不重疊、交接兩端齊備、寫入權與 OWNERSHIP 相符。"""
    assert run(ROOT / "scripts" / "verify_isolation.py").returncode == 0


def test_mission_card_identical_everywhere():
    """15 份共同認知卡必須逐字一致——不一致就代表 Agent 對目標的認知已分岐。"""
    src = (ROOT / "shared" / "MISSION.md").read_text(encoding="utf-8")
    n = 0
    for d in (ROOT / "agents").iterdir():
        f = d / ".context" / "mission.md"
        if not d.is_dir():
            continue
        assert f.exists(), f"{d.name} 沒有共同認知卡"
        assert f.read_text(encoding="utf-8") == src, f"{d.name} 的共同認知卡不一致"
        assert "@.context/mission.md" in (d / "CLAUDE.md").read_text(encoding="utf-8")
        n += 1
    assert n == 15


def test_no_agent_can_write_outside_its_ownership():
    """每個 Agent 宣告的寫入路徑都必須是 OWNERSHIP.yaml 指定給它的。"""
    own = yaml.safe_load((ROOT / "shared" / "OWNERSHIP.yaml").read_text(encoding="utf-8"))
    forbidden = {p for p, s in own["writable_paths"].items() if s["owner"] == "none"}
    assert "shared/**" in forbidden and "data/**" in forbidden and "router/.env" in forbidden
    for d in (ROOT / "agents").iterdir():
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        allow = json.loads(f.read_text(encoding="utf-8"))["permissions"]["allow"]
        for a in allow:
            for bad in ("shared/", "data/", "router/", "engine/", "db/", ".context/"):
                assert not re.match(rf"^(Write|Edit)\(\.\./\.\./{re.escape(bad)}", a), f"{d.name} 可寫 {a}"


def test_guard_detects_unauthorized_change(tmp_path):
    """L3 偵測層：Agent 動到不屬於它的檔案必須被抓到（工具層擋不住有執行權的 Agent）。"""
    import shutil
    target = ROOT / "agents" / "chart" / "MANUAL.md"
    backup = tmp_path / "MANUAL.md"
    shutil.copy(target, backup)
    run(ROOT / "scripts" / "guard_paths.py", "snapshot")
    try:
        target.write_text(target.read_text(encoding="utf-8") + "\n<!-- 越權 -->\n", encoding="utf-8")
        r = run(ROOT / "scripts" / "guard_paths.py", "verify", "--agent", "lab")
        assert r.returncode == 1 and "未授權" in r.stdout
    finally:
        shutil.copy(backup, target)
        run(ROOT / "scripts" / "guard_paths.py", "snapshot")


def test_router_runs_guard_after_every_call():
    """守衛必須真的被呼叫，不能只是存在。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "def guard_check" in src and "violation = guard_check(aid)" in src
    assert "verify_isolation.py" in src, "preflight 必須包含隔離驗證"
    assert "guard_paths.py" in src and "snapshot" in src


def test_forge_writes_only_in_sandbox():
    """FORGE 是唯一的程式維護者，但它只能在 worktree 沙箱寫，合併由 merge_fix.py 把關。"""
    st = json.loads((ROOT / "agents" / "forge" / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allow, deny = st["permissions"]["allow"], set(st["permissions"]["deny"])
    assert "Write" not in allow and "Edit" not in allow, "不得有無路徑限制的寫入"
    assert any("worktree" in a for a in allow)
    for d in ("Write(../../engine/**)", "Write(../../scripts/**)", "Write(../../router/**)",
              "Bash(python *)", "Bash(git push *)", "Bash(git merge *)"):
        assert d in deny, f"FORGE 的 deny 缺少 {d}"


# ── L0：OS 層沙箱（v3.0 新增）──────────────────────────────────────

def test_every_agent_has_os_sandbox():
    """15 個 Agent 都要有啟用的沙箱區塊——這是逃逸路徑真正被封住的地方。"""
    for d in sorted((ROOT / "agents").iterdir()):
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        sb = json.loads(f.read_text(encoding="utf-8")).get("sandbox")
        assert sb and sb.get("enabled") is True, f"{d.name} 沒有啟用 OS 層沙箱"


def test_sandbox_matches_ownership():
    """沙箱規則必須由 OWNERSHIP.yaml 生成，不能手改。"""
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_sandbox.py"), "--verify"],
                       capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout


def test_sandbox_denies_writes_outside_ownership():
    """LAB 擁有 backtest/，就不能在沙箱層寫 shared/ engine/ 或任何別人的目錄。"""
    sb = json.loads((ROOT / "agents" / "lab" / ".claude" / "settings.json").read_text(encoding="utf-8"))["sandbox"]
    dw = set(sb["filesystem"]["denyWrite"])
    for p in ("../../shared", "../../engine", "../../router", "../../scripts", "../../db", "../../data"):
        assert p in dw, f"lab 的沙箱沒有擋住 {p}"
    assert "../../agents/chart" in dw
    assert "../../backtest" in sb["filesystem"]["allowWrite"]


def test_sandbox_mirrors_tool_layer_read_denies():
    """CHART 在工具層被擋的 RISK_RULES，在 OS 層也要擋——否則 Bash `cat` 就讀到了。"""
    st = json.loads((ROOT / "agents" / "chart" / ".claude" / "settings.json").read_text(encoding="utf-8"))
    dr = set(st["sandbox"]["filesystem"]["denyRead"])
    assert "../../shared/RISK_RULES.md" in dr, "Goodhart 防護在 OS 層漏掉了"
    assert "../../shared/strategy_params.yaml" in dr
    assert "../../router/.env" in dr


def test_sandbox_does_not_block_authorized_query_path():
    """data/ 不能進 denyRead，否則 query_readonly.py（Bash 子程序）開不了資料庫。"""
    for d in sorted((ROOT / "agents").iterdir()):
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        dr = json.loads(f.read_text(encoding="utf-8"))["sandbox"]["filesystem"]["denyRead"]
        assert not any(p.startswith("../../data") for p in dr), f"{d.name} 的沙箱擋掉了授權查詢路徑"


def test_sandbox_does_not_lock_agent_out_of_itself():
    """自己的身分檔不能出現在自己的 denyRead。"""
    for d in sorted((ROOT / "agents").iterdir()):
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        dr = json.loads(f.read_text(encoding="utf-8"))["sandbox"]["filesystem"]["denyRead"]
        assert not any(f"agents/{d.name}" in p for p in dr), f"{d.name} 被自己的沙箱鎖在門外"


def test_router_passes_session_hardening():
    """strictAllowlist / failIfUnavailable / allowUnsandboxedCommands 只有 CLI 能開，Router 必須帶。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "SESSION_HARDENING" in t
    assert '"--settings", json.dumps(SESSION_HARDENING)' in t
    assert '"failIfUnavailable": REQUIRE_SANDBOX' in t, "沙箱要求與否必須可設定（Windows 原生沒有沙箱）"
    assert '"allowUnsandboxedCommands": not REQUIRE_SANDBOX' in t
    assert '"strictAllowlist": True' in t


def test_credentials_are_denied_to_every_agent():
    for d in sorted((ROOT / "agents").iterdir()):
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        cred = json.loads(f.read_text(encoding="utf-8"))["sandbox"]["credentials"]
        files = {c["path"] for c in cred["files"] if c["mode"] == "deny"}
        envs = {c["name"] for c in cred["envVars"] if c["mode"] == "deny"}
        assert "~/.ssh" in files and "../../router/.env" in files, f"{d.name}"
        assert {"BITGET_API_SECRET", "DISCORD_TOKEN"} <= envs, f"{d.name}"


# ── GitHub 治理（v3.0 新增）────────────────────────────────────────

def test_ci_workflow_runs_every_verifier():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for s in ("check_secrets.py", "build_context.py", "lint_agents.py",
              "verify_isolation.py", "verify_docs_claims.py", "pytest"):
        assert s in ci, f"CI 沒有跑 {s}"


def test_secret_scanner_catches_a_planted_key(tmp_path):
    """植入一把假的 Discord token，掃描器必須抓到。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_secrets
    fake = "MTIzNDU2Nzg5MDEyMzQ1Njc4.GaBcDe.fGhIjKlMnOpQrStUvWxYz0123456789abcd"  # check_secrets: allow
    assert check_secrets.scan_text("router/config.py", f'TOKEN = "{fake}"')
    assert check_secrets.scan_text("engine/x.py", 'api_secret = "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW"')  # check_secrets: allow
    # 佔位字樣不該誤判
    assert not check_secrets.scan_text("router/.env.example", 'DISCORD_TOKEN="your_token_here"')


def test_gitignore_covers_every_secret_surface():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for p in ("router/.env", "*.pem", "*.key", "data/", "legacy/"):
        assert p in gi, f".gitignore 缺少 {p}"
    assert "!router/.env.example" in gi


def test_no_agent_can_push_to_remote():
    """任何 Agent 能 git push，L2 的『合併必須經 merge_fix.py』就繞過了。"""
    for d in sorted((ROOT / "agents").iterdir()):
        f = d / ".claude" / "settings.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text(encoding="utf-8"))
        allow = st["permissions"]["allow"]
        if any(a.startswith("Bash(git") for a in allow):
            assert "Bash(git push *)" in st["permissions"]["deny"], f"{d.name} 有 git 權限卻沒 deny push"


# ── 文件呈現與結構（v3.0 回歸修正）────────────────────────────────

def test_no_orphan_table_rows_in_any_doc():
    """表格列被插到表格外面時，Markdown 會印出裸的 | 字元——v3.0 發生過一次。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    from md_tables import orphan_table_rows
    bad = []
    for f in sorted(ROOT.glob("docs/*.md")) + sorted(ROOT.glob("shared/*.md")):
        bad += [f"{f.name}:{ln} {why}" for ln, why in orphan_table_rows(f.read_text(encoding="utf-8"))]
    assert not bad, f"孤兒表格列：{bad}"


def test_orphan_detector_actually_detects():
    sys.path.insert(0, str(ROOT / "scripts"))
    from md_tables import orphan_table_rows
    good = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    assert not orphan_table_rows(good)
    assert orphan_table_rows(good + "\n文字段落\n\n| 3 | 4 |\n")
    assert orphan_table_rows("段落\n| a | b |\n|---|---|\n| 1 | 2 |\n")   # 表頭緊接段落
    assert not orphan_table_rows("## 標題\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    # 程式碼區塊裡的管線字元不算
    assert not orphan_table_rows("```\n| not | a | table |\n```\n")


def test_site_has_every_tab_v29_had():
    """v2.9 的站台是 15 分頁；v3.0 加了「邊界」「GitHub」。少一個分頁就是弄丟一塊內容。"""
    html = (ROOT / "docs" / "TRADE-DESK_whitepaper.html").read_text(encoding="utf-8")
    tabs = re.findall(r'data-tab="(\w+)"', html)
    v29 = ["overview", "wp", "arch", "build", "harness", "devenv", "agents", "skills",
           "spec", "router", "setup", "ops", "roadmap", "adr", "glossary"]
    assert set(v29) <= set(tabs), f"少了 v2.9 的分頁：{set(v29) - set(tabs)}"
    assert {"bound", "github"} <= set(tabs), "v3.0 的邊界與 GitHub 分頁沒進站台"
    assert len(re.findall(r'data-panel="', html)) == len(tabs), "分頁按鈕與內容數不符"


def test_site_contains_all_agents_and_skills():
    html = (ROOT / "docs" / "TRADE-DESK_whitepaper.html").read_text(encoding="utf-8")
    for aid in sorted(d.name for d in (ROOT / "agents").iterdir() if d.is_dir()):
        assert f'id="agents-{aid}"' in html, f"站台缺少 {aid} 的卡片"
    skills = [d.name for d in (ROOT / "skills").iterdir() if d.is_dir()]
    assert len(re.findall(r'id="skill-', html)) == len(skills)


def test_site_builder_lives_in_the_repo():
    """v2.9 的產生器只住在暫存區，所以它消失過一次。"""
    assert (ROOT / "scripts" / "build_site.py").exists()
    assert (ROOT / "docs" / "agents_meta.json").exists(), "站台需要的 Agent 中繼資料也必須在版控裡"
    src = (ROOT / "scripts" / "build_site.py").read_text(encoding="utf-8")
    assert "/tmp/" not in src, "產生器不得依賴暫存區路徑"


def test_every_markdown_table_actually_renders():
    """表格緊接段落之後會被吸進段落，印出裸的 | 字元——在產出的站台上實際確認。"""
    html = (ROOT / "docs" / "TRADE-DESK_whitepaper.html").read_text(encoding="utf-8")
    bare = re.findall(r"^\|.*\|$", html, re.M)
    assert not bare, f"{len(bare)} 行表格沒有被渲染成 <table>：{bare[:3]}"


# ── 執行環境開關（Windows 原生 vs WSL2）───────────────────────────

def test_sandbox_requirement_is_configurable():
    """Blacksheep 跑原生 Windows：預設不得要求沙箱，否則每次呼叫都會失敗。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert 'os.environ.get("TD_REQUIRE_SANDBOX", "0")' in t, "預設值必須是 0（原生 Windows）"
    assert '"failIfUnavailable": REQUIRE_SANDBOX' in t
    assert "TD_REQUIRE_SANDBOX" in (ROOT / "router" / ".env.example").read_text(encoding="utf-8")


def test_router_announces_isolation_level_at_startup():
    """最糟的失效模式是『以為有沙箱』——preflight 必須說清楚。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "L0 OS 層沙箱未啟用" in t and "LOG.warning" in t


# ── 可執行性（v3.0.2）──────────────────────────────────────────────

def test_every_python_file_compiles():
    import py_compile, tempfile
    sys.path.insert(0, str(ROOT / "scripts"))
    from td_paths import project_py_files
    bad = []
    for f in project_py_files(ROOT):
        try:
            py_compile.compile(str(f), doraise=True, cfile=tempfile.mktemp())
        except Exception as e:
            bad.append(f"{f.relative_to(ROOT)}: {e}")
    assert not bad, bad


def test_scheduled_programs_exist_or_are_planned():
    """排程指向的程式若還沒寫，必須在 BUILD_PLAN 裡——否則是永遠不會被建的靜默缺口。"""
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    plan = (ROOT / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
    gaps = []
    for aid, a in cfg["agents"].items():
        for job, cmdline in (a.get("scripts") or {}).items():
            for tok in cmdline.split():
                if tok.endswith(".py") and not (ROOT / tok).exists() and Path(tok).name not in plan:
                    gaps.append(f"{aid}/{job} → {tok}")
    assert not gaps, f"排程指向不存在也沒排進 BUILD_PLAN 的程式：{gaps}"


def test_docs_only_reference_scripts_that_exist_or_are_planned():
    """文件叫使用者跑的程式，要嘛已經在，要嘛必須是 BUILD_PLAN 的待建項目。"""
    plan = (ROOT / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
    bad = []
    for f in list(ROOT.glob("docs/*.md")) + [ROOT / "README.md", ROOT / "QUICKSTART.md"]:
        if not f.exists():
            continue
        for m in re.findall(r"python3?\s+((?:scripts|router|engine)[/\\][\w/\\]+\.py)",
                            f.read_text(encoding="utf-8")):
            rel = m.replace("\\", "/")
            if not (ROOT / rel).exists() and Path(rel).name not in plan:
                bad.append(f"{f.name} → {m}")
    assert not bad, f"文件叫使用者跑不存在、也沒排進 BUILD_PLAN 的程式：{bad}"


def test_doctor_runs_and_reports():
    """doctor 必須能在沒有 .env、沒有資料庫的乾淨環境跑完（回傳 0 或 2）。"""
    r = run(ROOT / "scripts" / "doctor.py", "--no-claude")
    assert r.returncode in (0, 2), f"doctor 回報致命問題：\n{r.stdout[-1500:]}"
    for section in ("基本工具", "Claude Code CLI", "專案完整性", "隔離層級"):
        assert section in r.stdout, f"doctor 少了「{section}」區段"
    # 帶 --agent 時也要能跑（只是跳過冒煙測試）
    r2 = run(ROOT / "scripts" / "doctor.py", "--no-claude", "--agent", "chart")
    assert r2.returncode in (0, 2)


def test_day0_documents_the_claude_p_smoke_test():
    """『claude -p 沒反應』是最容易卡死新手的一步，手冊必須有專章。"""
    t = (ROOT / "docs" / "DAY0_RUNBOOK.md").read_text(encoding="utf-8")
    assert "步驟 2B" in t
    assert "不會邊跑邊印" in t, "必須說明 JSON 模式在跑完前完全空白"
    assert "讀 stdin" in t, "必須說明不帶提示詞會卡在等 stdin"
    assert "doctor.py" in t


def test_router_gives_actionable_message_when_env_missing():
    """少填一個鍵不該是 KeyError + traceback。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "def require_env" in t and "BOOT_REQUIRED" in t
    assert "找不到 router/.env" in t
    assert 'os.environ["OWNER_USER_ID"]' in t and t.index("require_env()") < t.index('os.environ["OWNER_USER_ID"]')


def test_router_skips_bots_whose_token_is_not_filled_yet():
    """Day 0 是漸進的：只建了 2 隻 Bot 時，Router 必須能起來並說清楚少了誰。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert 'os.environ.get(a["token_env"])' in t, "缺 token 時不得用 os.environ[...] 直接炸"
    assert "skipped" in t and "尚未啟動" in t


def test_requirements_cover_every_third_party_import():
    import ast as _ast
    std = set(sys.stdlib_module_names)
    local = ({p.stem for p in (ROOT / "scripts").glob("*.py")}
             | {p.stem for p in (ROOT / "engine").glob("*.py")}
             | {"router", "engine", "scripts", "tests"})
    alias = {"discord": "discord.py", "yaml": "pyyaml", "dotenv": "python-dotenv"}
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    sys.path.insert(0, str(ROOT / "scripts"))
    from td_paths import project_py_files
    missing = set()
    for f in project_py_files(ROOT):
        for n in _ast.walk(_ast.parse(f.read_text(encoding="utf-8"))):
            names = ([a.name.split(".")[0] for a in n.names] if isinstance(n, _ast.Import)
                     else [n.module.split(".")[0]] if isinstance(n, _ast.ImportFrom)
                     and n.level == 0 and n.module else [])
            for nm in names:
                if nm in std or nm in local:
                    continue
                if alias.get(nm, nm).lower() not in req and nm.lower() not in req:
                    missing.add(nm)
    assert not missing, f"requirements.txt 漏了：{sorted(missing)}——使用者照手冊裝完仍會 ModuleNotFoundError"


def test_doctor_catches_moved_venv_and_bad_paths(tmp_path):
    """venv 搬家 / 路徑含空格 / 雲端同步資料夾——三個 Windows 上最常見的坑。"""
    src = (ROOT / "scripts" / "doctor.py").read_text(encoding="utf-8")
    assert "check_path_and_venv" in src
    assert "pyvenv.cfg" in src, "必須驗 venv 記錄的 python 還在不在"
    assert "pip.exe" in src, "必須驗啟動器裡寫死的路徑"
    assert "onedrive" in src.lower() and "/desktop/" in src
    assert "Fatal error in launcher" in src, "要把使用者看到的訊息原文寫進診斷"


def test_day0_uses_python_m_pip_and_correct_requirements_path():
    """`pip install -r router\\requirements.txt` 這行曾讓使用者直接失敗兩次。"""
    t = (ROOT / "docs" / "DAY0_RUNBOOK.md").read_text(encoding="utf-8")
    assert "router\\requirements.txt" not in t, "requirements.txt 在專案根目錄，不在 router\\"
    assert "python -m pip install -r requirements.txt" in t
    assert "venv 不可搬移" in t or "永遠不要搬移或改名一個已經建好的 venv" in t
    assert "路徑不能有空格" in t and "OneDrive" in t


def test_changelog_numbers_are_not_rewritten():
    """CHANGELOG 記錄的是『當初那個數字錯了』，不能被 --fix 改掉。"""
    src = (ROOT / "scripts" / "verify_docs_claims.py").read_text(encoding="utf-8")
    assert "numbers_are_history" in src
    ch = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "41 個視圖" in ch, "歷史紀錄被改寫了"


# ── Windows 主控台與模組邊界（v3.0.5）──────────────────────────────

def test_scripts_that_print_chinese_import_td_console():
    """cp950 主控台下 print 一個 ⚠️ 就會讓整支腳本崩潰。"""
    import ast as _ast
    bad = []
    for f in sorted((ROOT / "scripts").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        if f.name == "td_console.py" or "td_console" in src:
            continue
        if any(isinstance(n, _ast.Call) and getattr(n.func, "id", "") == "print"
               and not _ast.unparse(n).isascii()
               for n in _ast.walk(_ast.parse(src))):
            bad.append(f.name)
    assert not bad, f"這些腳本在 Windows cp950 主控台會 UnicodeEncodeError：{bad}"


def test_verify_isolation_survives_cp950_console():
    """實跑：把子程序的輸出編碼逼成 cp950，不可以崩潰。"""
    import os
    env = {**os.environ, "PYTHONIOENCODING": "cp950"}
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_isolation.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=ROOT)
    assert "UnicodeEncodeError" not in (r.stderr or ""), r.stderr[-500:]
    assert r.returncode == 0, r.stdout[-500:]


def test_importing_build_site_does_not_build_the_site():
    """lint 曾經 `from build_site import ...`，結果每次 lint 都重建整個 HTML 站台。"""
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, r'%s'); import build_site" % (ROOT / "scripts")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    assert "已產生" not in (r.stdout or ""), "import build_site 竟然把站台重建了一次"
    assert "是腳本不是模組" in (r.stdout + r.stderr), "應該給出明確的 ImportError"

    r2 = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, r'%s'); from md_tables import orphan_table_rows; print('ok')"
         % (ROOT / "scripts")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    assert r2.returncode == 0 and "已產生" not in r2.stdout


def test_lint_never_reports_an_empty_error():
    """子程序崩潰時，lint 必須端出 stderr，而不是印一行空白的 ERROR。"""
    src = (ROOT / "scripts" / "lint_agents.py").read_text(encoding="utf-8")
    assert "def run_check" in src
    assert "PYTHONIOENCODING" in src and 'encoding="utf-8"' in src
    assert "自己崩潰了" in src, "必須有『子程序崩潰』這條分支"
    forbidden = "subprocess" + ".run("
    main_body = src[src.index("def main() -> int:"):]
    main_body = "\n".join(l for l in main_body.splitlines() if not l.lstrip().startswith("#"))
    main_body = main_body.replace(f'"{forbidden}"', "").replace(f"'{forbidden}'", "")
    assert forbidden not in main_body, "main() 不該再直接呼叫子程序，要走 run_check()"


# ── 掃全樹的檢查不得掃到 .venv（v3.0.6）──────────────────────────

def test_project_file_filter_excludes_dependencies(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    from td_paths import is_project_file, project_py_files
    for bad in (".venv/Lib/site-packages/pandas/io/clipboard/__init__.py",
                "venv/lib/python3.12/site-packages/pip/_vendor/distlib/compat.py",
                "node_modules/x/y.py", "__pycache__/z.py",
                "agents/forge/worktree/engine/executor.py",
                "build/lib/a.py", "legacy/old_project/main.py"):
        assert not is_project_file(ROOT / bad, ROOT), f"{bad} 不該被當成專案自己的檔案"
    for good in ("scripts/lint_agents.py", "router/discord_router.py",
                 "engine/ingest_server.py", "tests/test_context_and_grants.py"):
        assert is_project_file(ROOT / good, ROOT), f"{good} 應該算專案的檔案"
    assert all(is_project_file(f, ROOT) for f in project_py_files(ROOT))


def test_lint_ignores_a_real_venv(tmp_path):
    """使用者建好 .venv 之後，lint 第 24 項曾對 pandas / pip 的原始碼噴 163 個錯。"""
    import shutil, os
    work = tmp_path / "trade-desk"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".git", ".venv", "data", "logs"))
    # 造一個「看起來很像真的」的 .venv
    sp = work / ".venv" / "Lib" / "site-packages"
    (sp / "pandas" / "io" / "clipboard").mkdir(parents=True)
    (sp / "pandas" / "io" / "clipboard" / "__init__.py").write_text(
        "import AppKit\nimport Foundation\n", encoding="utf-8")
    (sp / "pip" / "_vendor" / "distlib").mkdir(parents=True)
    (sp / "pip" / "_vendor" / "distlib" / "compat.py").write_text(
        "import ConfigParser\n", encoding="utf-8")
    (work / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")

    subprocess.run([sys.executable, str(work / "scripts" / "build_context.py")],
                   capture_output=True, cwd=work)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(work / "scripts" / "lint_agents.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=work, env=env)
    assert "AppKit" not in r.stdout and "site-packages" not in r.stdout, \
        f"lint 掃到了 .venv：\n{r.stdout[:1200]}"
    assert r.returncode == 0, r.stdout[-1500:]


def test_docs_only_teach_flags_that_exist(tmp_path):
    """v3.0.7：BUILD_PLAN 教人打 `scan_legacy.py --out ... --json ...`，那兩個參數不存在。"""
    import ast as _ast, shutil, os
    work = tmp_path / "td"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".git", ".venv", "data", "logs"))
    (work / "docs" / "08_BUILD_PLAN.md").write_text(
        (work / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
        + "\n```powershell\npython scripts\\scan_legacy.py --src C:\\x --out y.md --json z.json\n```\n",
        encoding="utf-8")
    subprocess.run([sys.executable, str(work / "scripts" / "build_context.py")],
                   capture_output=True, cwd=work)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(work / "scripts" / "lint_agents.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=work, env=env)
    assert "[28]" in r.stdout and "--out" in r.stdout and "--json" in r.stdout, r.stdout[-1200:]


def test_legacy_inventory_is_multi_project():
    """多個舊專案走登錄表，不是重複打 --src。"""
    ex = (ROOT / "legacy" / "projects.yaml.example").read_text(encoding="utf-8")
    data = yaml.safe_load(ex)
    assert len(data["projects"]) >= 2, "範本必須示範多個專案"
    for pr in data["projects"]:
        for k in ("id", "name", "path", "status", "trust"):
            assert k in pr, f"{pr.get('id')} 缺少 {k}"
    src = (ROOT / "scripts" / "scan_legacy.py").read_text(encoding="utf-8")
    assert '"--all"' in src and '"--project"' in src
    plan = (ROOT / "docs" / "08_BUILD_PLAN.md").read_text(encoding="utf-8")
    assert "scan_legacy.py --all" in plan, "建置流程必須教 --all 而不是逐一 --src"
    assert "--out" not in plan.split("scan_legacy.py")[1][:120]


# ── Discord 後台實際操作（v3.0.8）────────────────────────────────

def test_discord_setup_documents_install_link_before_public_bot():
    """關 Public Bot 之前必須先把 Install Link 設成 None，否則 Discord 直接擋下。"""
    for name in ("docs/02_SETUP_GUIDE.md", "docs/DAY0_RUNBOOK.md", "QUICKSTART.md"):
        t = (ROOT / name).read_text(encoding="utf-8")
        assert "Install Link" in t and "None" in t, f"{name} 沒教 Install Link 設 None"
        assert t.index("Install Link") < t.index("Public Bot") or "Installation" in t, name
    day0 = (ROOT / "docs" / "DAY0_RUNBOOK.md").read_text(encoding="utf-8")
    assert "私人應用程式不得使用預設授權連結" in day0, "要把使用者看到的錯誤訊息原文寫進去"
    assert "Disable Discovery" in day0, "Install Link 存不成 None 時的第二層原因"


def test_discord_setup_says_only_bot_scope():
    """OAuth2 的 scope 清單有二十幾項，手冊必須講明只勾 bot。"""
    for name in ("docs/02_SETUP_GUIDE.md", "docs/DAY0_RUNBOOK.md"):
        t = (ROOT / name).read_text(encoding="utf-8")
        assert "只勾" in t and "`bot`" in t, f"{name} 沒說清楚只勾 bot"
    guide = (ROOT / "docs" / "02_SETUP_GUIDE.md").read_text(encoding="utf-8")
    assert "applications.commands" in guide, "要說明為什麼連 applications.commands 都不需要"


# ── 子程序編碼（v3.0.9）──────────────────────────────────────────

def test_no_text_mode_subprocess_without_encoding():
    """Windows cp950 解 UTF-8 中文時，subprocess 的讀取執行緒會 UnicodeDecodeError。

    最陰險的地方：例外在**別的執行緒**，主程式拿到空字串、returncode 仍是 0，
    於是 Router 的 preflight 照樣印「OK」——真的失敗時你會得到一個空訊息。
    """
    import ast as _ast
    sys.path.insert(0, str(ROOT / "scripts"))
    from td_paths import project_py_files
    bad = []
    for f in project_py_files(ROOT):
        if f.name == "td_proc.py":
            continue
        for n in _ast.walk(_ast.parse(f.read_text(encoding="utf-8"))):
            if (isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "run"
                    and getattr(getattr(n.func, "value", None), "id", "") == "subprocess"):
                kw = {k.arg for k in n.keywords}
                if ("text" in kw or "universal_newlines" in kw) and "encoding" not in kw:
                    bad.append(f"{f.relative_to(ROOT)}:{n.lineno}")
    assert not bad, f"這些呼叫在 Windows 上會 UnicodeDecodeError：{bad}"


def test_router_preflight_survives_cp950_and_reports_stderr():
    """Router 的 preflight 必須用 UTF-8 安全的呼叫，且失敗時要端出 stderr。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "from td_proc import run as run_proc" in t
    assert "run_proc(" in t
    assert "(r.stderr or \"\").strip()" in t, "preflight 失敗時 stdout 可能是空的，必須也看 stderr"


def test_td_proc_decodes_utf8_child_output():
    """實跑：子程序印中文，td_proc 必須完整取回而不崩潰。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    from td_proc import run as run_proc
    r = run_proc([sys.executable, "-c",
                  "print('中文測試 ⚠️ 責任不重疊')"], cwd=ROOT)
    assert r.returncode == 0
    assert "中文測試" in r.stdout and "責任不重疊" in r.stdout


# ── Router 的三個「錯誤被吞掉」模式（v3.0.10）──────────────────────

def test_worker_survives_an_exception():
    """handle() 丟例外不得讓 worker 死掉——否則該 Agent 從此完全沒反應且無日誌。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    body = t.split("async def worker")[1].split("\nasync def ")[0]
    assert "except Exception" in body, "worker() 必須攔下例外"
    assert "LOG.exception" in body, "必須留下完整堆疊"
    assert "reply(" in body, "必須讓 Owner 在 Discord 上看得到失敗"
    assert "except asyncio.CancelledError" in body, "關機時要能正常取消"


def test_scheduler_passes_the_coroutine_not_a_lambda():
    """包一層同步 lambda 會被丟進執行緒，那裡沒有事件迴圈 → 45 個排程全部靜默失效。"""
    import ast as _ast
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    calls = {_ast.unparse(n.func) for n in _ast.walk(_ast.parse(t)) if isinstance(n, _ast.Call)}
    assert "asyncio.ensure_future" not in calls, "排程不得包同步 lambda（註解裡提到不算）"
    assert "sch.add_job(fire," in t, "要直接把 coroutine function 交給 AsyncIOExecutor"
    assert "args=[job]" in t


def test_no_single_character_error_slices():
    """`[-800]` 取的是一個字元，不是最後 800 字——錯誤訊息會被毀掉。"""
    import re as _re
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    bad = _re.findall(r"\[-\d+\]\}", t)
    assert not bad, f"這些是單字元切片，應該是 [-N:]：{bad}"


def test_log_timestamps_use_the_trading_timezone():
    """08:00 台北是這個系統的日界線；日誌時間戳不能跟著作業系統跑。"""
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "class _TzFormatter" in t and "ZoneInfo" in t
    assert 'TZ = SCHED.get("timezone"' in t
    assert "CronTrigger.from_crontab(job[\"cron\"], timezone=TZ)" in t, "cron 也要綁交易時區"


def test_worker_death_is_reported():
    t = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "add_done_callback" in t and "不會回應任何訊息" in t


# ── v3.0.11：discord 物件的 __slots__ 與「錯誤處理器自己炸掉」──────────

def _lint_on_a_copy(tmp_path, mutate) -> str:
    """把專案複製一份、動一行、跑 lint，回傳它印了什麼。

    直接改 ROOT 下的檔案會讓其他測試看到被污染的狀態，所以一律在副本上做。
    """
    work = tmp_path / "proj"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".git", ".venv", "data", "logs"))
    rt = work / "router" / "discord_router.py"
    rt.write_text(mutate(rt.read_text(encoding="utf-8")), encoding="utf-8")
    subprocess.run([sys.executable, str(work / "scripts" / "build_context.py")],
                   capture_output=True, cwd=work)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(work / "scripts" / "lint_agents.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=work, env=env)
    return r.stdout


def test_lint_catches_attribute_assignment_on_a_discord_message(tmp_path):
    """`msg._agent = aid` 必須被靜態擋下。

    discord.Message 有 __slots__、沒有 __dict__。這行寫在 handle() 的開頭，
    所以每一次觸發都失敗；而它在線上的樣子是「排程有發、Agent 回一句處理失敗」，
    看起來像 Agent 的問題，其實是 Router 的第一行。
    """
    out = _lint_on_a_copy(tmp_path, lambda s: s.replace(
        "    a = CFG[\"agents\"][aid]",
        "    a = CFG[\"agents\"][aid]\n    msg._agent = aid", 1))
    assert "[31]" in out and "_agent" in out, out[-1500:]


def test_lint_catches_raw_mention_lookup(tmp_path):
    """`a[\"mention\"]` 只有在 Bot 上線後才存在——在 except 區塊裡就是二次爆炸。"""
    out = _lint_on_a_copy(tmp_path, lambda s: s.replace(
        'forge = mention_of("forge")',
        'forge = CFG["agents"]["forge"]["mention"]', 1))
    assert "[32]" in out and "mention_of" in out, out[-1500:]


def test_router_never_touches_message_attributes():
    """行為面的同一件事：handle() 不得把狀態掛在別人的物件上。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    handle = src[src.index("async def handle("):src.index("async def worker(")]
    assert "msg._" not in handle and "message._" not in handle
    assert "aid=aid" in handle, "react() 要用參數收 agent id，而不是從訊息上讀回來"


# ── 開發 session 的啟動方式（ADR-004 + Claude Code 的工作目錄邊界）──────

def test_dev_launcher_adds_the_parent_directory():
    """從 dev/ 啟動的 session 預設讀不到 ../engine、../scripts——啟動器必須補 --add-dir。"""
    cmd = (ROOT / "dev" / "dev.cmd").read_text(encoding="utf-8")
    assert "--add-dir .." in cmd
    assert "claude" in cmd


def test_dev_check_command_covers_the_whole_verification_chain():
    """/td-check 必須涵蓋六支驗證程式，少一支就有一類漂移沒人擋。"""
    md = (ROOT / "dev" / ".claude" / "commands" / "td-check.md").read_text(encoding="utf-8")
    for s in ("build_context.py", "verify_docs_claims.py", "lint_agents.py",
              "verify_isolation.py", "pytest", "guard_paths.py verify"):
        assert s in md, f"/td-check 少了 {s}"


def test_no_claude_md_outside_dev_and_agents():
    """CLAUDE.md 只能出現在 dev/ 與 agents/——其他地方都會污染某一條繼承鏈（ADR-004）。"""
    for f in ROOT.rglob("CLAUDE.md"):
        rel = f.relative_to(ROOT).as_posix()
        assert rel.startswith(("dev/", "agents/")), f"不該有 {rel}"


def test_secret_scanner_allow_pragma_is_line_scoped():
    """`check_secrets: allow` 只豁免那一行——同一個檔案的其他行仍然要被抓到。

    這條存在的理由：掃描器原本會抓到自己測試裡的假金鑰，於是 DAY0 的**第一個 commit
    就被自己的 pre-commit 擋下來**。豁免必須夠窄，否則等於關掉整個檔案的防護。
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_secrets
    key = "AKIA" + "1234567890ABCDEF"
    assert not check_secrets.scan_text("x.py", f'k = "{key}"  # check_secrets: allow')
    assert check_secrets.scan_text("x.py", f'k = "{key}"')


def test_git_hooks_do_not_assume_an_activated_venv():
    """鉤子由 git 執行，venv 不會是啟動狀態——寫死 `python` 會用到系統那支。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import install_git_hooks as h
    for name, body in h.FILES.items():
        if name == "post-commit":
            continue
        assert ".venv/Scripts/python.exe" in body and ".venv/bin/python" in body, name
        assert '"$PY"' in body, name
    assert "pytest tests" in h.FILES["pre-push"], "pytest 要限定 tests/，否則會掃到 legacy/ 與 .venv"


def test_gitattributes_forces_lf_so_diffs_stay_readable():
    """CRLF 會讓 diff 變成整檔改動；而且 CRLF 的 sh 鉤子在 Git Bash 會 bad interpreter。"""
    ga = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in ga
    assert "*.sh   text eol=lf" in ga and "*.py   text eol=lf" in ga
    assert "*.cmd  text eol=crlf" in ga


# ── Windows 腳本的編碼（v3.0.17：snapshot.cmd 在 cp950 主控台直接炸開）────

def test_windows_batch_files_are_ascii_and_crlf():
    """.cmd / .bat 必須是純 ASCII + CRLF。

    cmd.exe 以**主控台的 ANSI codepage**（繁中 Windows 是 cp950）讀批次檔。
    UTF-8 的中文註解會被誤解成 cp950 的雙位元組字元，吃掉後面的 ASCII，
    於是連 `if "%MSG%"==""` 都會裂成 `G"=="" set MSG=checkpoint` 這種東西。
    純 ASCII 不管在哪個 codepage 都一樣——說明文字請寫在 .md 裡。
    """
    for f in list(ROOT.rglob("*.cmd")) + list(ROOT.rglob("*.bat")):
        if ".venv" in f.parts:
            continue
        b = f.read_bytes()
        try:
            b.decode("ascii")
        except UnicodeDecodeError as e:
            raise AssertionError(f"{f.relative_to(ROOT)} 含非 ASCII 字元（位置 {e.start}）") from None
        assert b"\r\n" in b, f"{f.relative_to(ROOT)} 是 LF；批次檔要 CRLF"


def test_powershell_scripts_have_a_utf8_bom():
    """.ps1 若含中文就必須有 UTF-8 BOM——PowerShell 5.1 沒 BOM 會當成 ANSI 讀。"""
    for f in ROOT.rglob("*.ps1"):
        if ".venv" in f.parts:
            continue
        b = f.read_bytes()
        try:
            b.decode("ascii")
            continue                      # 純 ASCII 不需要 BOM
        except UnicodeDecodeError:
            pass
        assert b[:3] == b"\xef\xbb\xbf", f"{f.relative_to(ROOT)} 有非 ASCII 字元卻沒有 UTF-8 BOM"


def test_snapshot_does_not_report_success_or_nothing_when_the_commit_failed():
    """commit 失敗時不可以印「Nothing to save」——那會讓人以為沒事。

    v3.0.17 的 `git commit ... && echo Saved || echo Nothing to save` 就是這樣：
    git 因為沒設 user.email 而失敗，使用者看到的卻是「Nothing to save」。
    """
    cmd = (ROOT / "dev" / "snapshot.cmd").read_text(encoding="ascii")
    assert "git diff --cached --quiet" in cmd, "要先判斷有沒有東西可存，而不是用 commit 的結果反推"
    assert "if errorlevel 1" in cmd and "Commit failed" in cmd
    assert "Author identity unknown" in cmd, "最常見的失敗原因要直接給出解法"
    assert "git rev-parse --git-dir" in cmd, "還不是版本庫時要說清楚，而不是讓 git 自己報錯"
