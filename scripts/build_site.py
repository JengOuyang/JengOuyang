#!/usr/bin/env python3
"""build_site.py — 產生 TRADE-DESK 的完整文件站台（單一離線 HTML）。

為什麼在 repo 裡：
    v2.9 以前這支程式只住在暫存區，換一次 session 就消失，
    結果 v3.0 交付時只能臨時重寫，把 15 個分頁弄成 1 個。
    呈現方式跟文件內容一樣需要單一真相，這就是它。

站台結構（v2.9 建立，v3.0 沿用並擴充）：
    總覽 / 白皮書 / 架構 / 建置流程 / 邊界 / GitHub / Harness / 開發環境
    / Agent（15 張卡，含 PERSONA + MANUAL）/ Skills / 規格（shared 全文）
    / Router（可執行程式全文）/ 教學 / 維運 / 路線圖 / ADR / 術語

用法：
    python scripts/build_site.py                 # → docs/TRADE-DESK_whitepaper.html
    python scripts/build_site.py --out x.html
"""
import markdown, re, os, json, sys, html as H
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台）
from md_tables import orphan_table_rows, check_tables, check_all_docs

# 這是頂層腳本：import 它會把整個站台重建一次。
# v3.0.5 之前 lint 就是這樣「順便」建站的（使用者跑 lint 卻看到「已產生 ...html」）。
if __name__ != "__main__":
    raise ImportError(
        "build_site.py 是腳本不是模組；表格檢查請 `from md_tables import orphan_table_rows`")

ROOT = str(Path(__file__).resolve().parents[1])
META = json.load(open(f"{ROOT}/docs/agents_meta.json", encoding="utf-8"))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"{ROOT}/docs/TRADE-DESK_whitepaper.html"
def md(p): return markdown.markdown(open(p,encoding="utf-8").read(),extensions=["tables","fenced_code","sane_lists"])
def slug(s): return re.sub(r'[^\w一-鿿]+','-',s).strip('-').lower()
def strip_h1(h): return re.sub(r'^<h1[^>]*>.*?</h1>\s*','',h,count=1,flags=re.S)
def sect(did,path,base=None):
    h=strip_h1(md(path)); navs=[]
    def rep(m):
        t=re.sub('<[^>]+>','',m.group(1)); sid=f"{did}-{slug(t)}"; navs.append((sid,t))
        return f'<h2 id="{sid}">{m.group(1)}</h2>'
    return re.sub(r'<h2[^>]*>(.*?)</h2>',rep,h,flags=re.S),navs
def code(path,lang=""): return f'<pre><code class="language-{lang}">{H.escape(open(path,encoding="utf-8").read())}</code></pre>'

if "--check" in sys.argv:
    raise SystemExit(check_all_docs())

navjson={}; panels=[]
for did,label,path in [("wp","白皮書",f"{ROOT}/docs/00_WHITEPAPER.md"),("arch","架構",f"{ROOT}/docs/01_ARCHITECTURE.md"),
                       ("day0","Day 0 手冊",f"{ROOT}/docs/DAY0_RUNBOOK.md"),("build","建置流程",f"{ROOT}/docs/08_BUILD_PLAN.md"),("gov","治理",f"{ROOT}/docs/10_CODE_GOVERNANCE.md"),("bound","數位邊界",f"{ROOT}/docs/12_DIGITAL_BOUNDARY.md"),("github","GitHub",f"{ROOT}/docs/13_GITHUB.md"),("harness","Harness 經驗",f"{ROOT}/docs/09_HARNESS_LESSONS.md"),("devenv","開發環境",f"{ROOT}/docs/04_DEV_ENVIRONMENT.md"),("setup","教學",f"{ROOT}/docs/02_SETUP_GUIDE.md"),
                       ("ops","維運",f"{ROOT}/docs/05_OPERATIONS.md"),("roadmap","路線圖",f"{ROOT}/docs/06_ROADMAP.md"),
                       ("legacy","資產複用",f"{ROOT}/docs/11_LEGACY_ASSETS.md"),("glossary","術語",f"{ROOT}/docs/07_GLOSSARY.md"),("changelog","變更紀錄",f"{ROOT}/docs/CHANGELOG.md")]:
    h,n=sect(did,path); navjson[did]=n; panels.append((did,label,h))

# 規格 panel（多份文件合併，各自一個 section）
spec_parts=[]; spec_nav=[]
for key,label,path in [("const","憲法",f"{ROOT}/shared/CONSTITUTION.md"),("proto","協作協定",f"{ROOT}/shared/PROTOCOL.md"),
                       ("risk","風控規則",f"{ROOT}/shared/RISK_RULES.md"),("metrics","績效量尺",f"{ROOT}/shared/METRICS_SPEC.md"),
                       ("data","資料 Schema",f"{ROOT}/shared/DATA_SCHEMA.md"),("mission","共同認知卡",f"{ROOT}/shared/MISSION.md"),("own","責任與權限",f"{ROOT}/shared/OWNERSHIP.yaml"),("opt","策略優化循環",f"{ROOT}/shared/OPTIMIZATION_CYCLE.md"),("mkt","行銷手冊",f"{ROOT}/shared/MARKETING_PLAYBOOK.md")]:
    sid=f"spec-{key}"; spec_nav.append((sid,label))
    spec_parts.append(f'<section class="agent" id="{sid}"><div class="agent-head"><span class="agent-code">{label}</span><span class="agent-model">shared/{os.path.basename(path)}</span></div>{strip_h1(md(path))}</section>')
for key,label,path,lang in [("universe","商品宇宙",f"{ROOT}/shared/universe.yaml","yaml"),("params","參數",f"{ROOT}/shared/strategy_params.yaml","yaml"),
                            ("cmap","切片規則",f"{ROOT}/shared/context_map.yaml","yaml"),("grants","視圖權限",f"{ROOT}/shared/view_grants.yaml","yaml"),
                            ("views","權限視圖 SQL",f"{ROOT}/db/002_views.sql","sql")]:
    sid=f"spec-{key}"; spec_nav.append((sid,label))
    spec_parts.append(f'<section class="agent" id="{sid}"><div class="agent-head"><span class="agent-code">{label}</span><span class="agent-model">{os.path.relpath(path,ROOT)}</span></div>{code(path,lang)}</section>')
navjson["spec"]=spec_nav; spec_html='<p class="lede">單一真相（shared/）。Agent 不直接讀這裡，而是讀由 build_context.py 生成的角色切片。</p>'+"".join(spec_parts)

# ADR
adr_parts=[]; adr_nav=[]
for f in sorted(os.listdir(f"{ROOT}/docs/adr")):
    if not f.startswith("ADR"): continue
    sid="adr-"+f.split("-")[1]; adr_nav.append((sid,f.replace(".md","")))
    adr_parts.append(f'<section class="agent" id="{sid}">{md(f"{ROOT}/docs/adr/{f}")}</section>')
navjson["adr"]=adr_nav; adr_html='<p class="lede">每個重要架構選擇的背景、被否決的方案、後果，以及何時該重新考慮。</p>'+"".join(adr_parts)

# Router
router_html=('<p class="lede">16 隻 Bot、佇列、排程、狀態表情、preflight 自檢。以下為可執行程式與設定全文。</p>'
 +'<h2 id="r-py">discord_router.py</h2>'+code(f"{ROOT}/router/discord_router.py","python")
 +'<h2 id="r-agents">agents.yaml</h2>'+code(f"{ROOT}/router/agents.yaml","yaml")
 +'<h2 id="r-sched">scheduler.yaml</h2>'+code(f"{ROOT}/router/scheduler.yaml","yaml")
 +'<h2 id="r-ctx">scripts/build_context.py</h2>'+code(f"{ROOT}/scripts/build_context.py","python")
 +'<h2 id="r-q">scripts/query_readonly.py</h2>'+code(f"{ROOT}/scripts/query_readonly.py","python")
 +'<h2 id="r-lint">scripts/lint_agents.py</h2>'+code(f"{ROOT}/scripts/lint_agents.py","python")
 +'<h2 id="r-close">scripts/daily_close_check.py</h2>'+code(f"{ROOT}/scripts/daily_close_check.py","python")
 +'<h2 id="r-sync">scripts/sync_manual_cron.py</h2>'+code(f"{ROOT}/scripts/sync_manual_cron.py","python")
 +'<h2 id="r-legacy">scripts/scan_legacy.py</h2>'+code(f"{ROOT}/scripts/scan_legacy.py","python")
 +'<h2 id="r-claims">scripts/verify_docs_claims.py</h2>'+code(f"{ROOT}/scripts/verify_docs_claims.py","python")
 +'<h2 id="r-env">router/.env.example</h2>'+code(f"{ROOT}/router/.env.example","bash")
 +'<h2 id="r-iso">scripts/verify_isolation.py</h2>'+code(f"{ROOT}/scripts/verify_isolation.py","python")
 +'<h2 id="r-guard">scripts/guard_paths.py</h2>'+code(f"{ROOT}/scripts/guard_paths.py","python")
 +'<h2 id="r-sandbox">scripts/sync_sandbox.py</h2>'+code(f"{ROOT}/scripts/sync_sandbox.py","python")
 +'<h2 id="r-secrets">scripts/check_secrets.py</h2>'+code(f"{ROOT}/scripts/check_secrets.py","python")
 +'<h2 id="r-hooks">scripts/install_git_hooks.py</h2>'+code(f"{ROOT}/scripts/install_git_hooks.py","python")
 +'<h2 id="r-backup">scripts/backup_mirror.py</h2>'+code(f"{ROOT}/scripts/backup_mirror.py","python")
 +'<h2 id="r-doctor">scripts/doctor.py</h2>'+code(f"{ROOT}/scripts/doctor.py","python")
 +'<h2 id="r-console">scripts/td_console.py</h2>'+code(f"{ROOT}/scripts/td_console.py","python")
 +'<h2 id="r-paths">scripts/td_paths.py</h2>'+code(f"{ROOT}/scripts/td_paths.py","python")
 +'<h2 id="r-proc">scripts/td_proc.py</h2>'+code(f"{ROOT}/scripts/td_proc.py","python")
 +'<h2 id="r-ci">.github/workflows/ci.yml</h2>'+code(f"{ROOT}/.github/workflows/ci.yml","yaml"))
navjson["router"]=[("r-py","discord_router.py"),("r-agents","agents.yaml"),("r-sched","scheduler.yaml"),("r-ctx","build_context.py"),("r-q","query_readonly.py"),("r-lint","lint_agents.py"),("r-close","daily_close_check.py"),("r-sync","sync_manual_cron.py"),("r-legacy","scan_legacy.py"),("r-claims","verify_docs_claims.py"),("r-env",".env.example"),("r-iso","verify_isolation.py"),("r-guard","guard_paths.py"),("r-sandbox","sync_sandbox.py"),("r-secrets","check_secrets.py"),("r-hooks","install_git_hooks.py"),("r-backup","backup_mirror.py"),("r-doctor","doctor.py"),("r-console","td_console.py"),("r-paths","td_paths.py"),("r-proc","td_proc.py"),("r-ci","ci.yml")]

# Agents
order=["ceo","macro","feed","ledger","chart","risk","exec","lab","redteam","audit","watch","forge","cmo","creative","growth"]
ag=[];agn=[]
for aid in order:
    m=META[aid]; sid=f"agents-{aid}"; agn.append((sid,f"{m['name']} · {m['cn']}"))
    ctx=sorted(os.path.basename(x) for x in os.listdir(f"{ROOT}/agents/{aid}/.context") if x.endswith(".md"))
    ag.append(f'<section class="agent" id="{sid}"><div class="agent-head"><span class="agent-code">{m["name"]}</span><span class="agent-title">{m["cn"]}</span><span class="dept">{m["dept"]}</span><span class="agent-model">{m["kind"]} · {m["model"]}</span></div>'
      f'<p class="ctxline">上下文切片：{" · ".join(ctx)}</p>'
      f'<details open><summary>PERSONA.md — 人設</summary>{strip_h1(md(f"{ROOT}/agents/{aid}/PERSONA.md"))}</details>'
      f'<details><summary>MANUAL.md — 作業手冊</summary>{strip_h1(md(f"{ROOT}/agents/{aid}/MANUAL.md"))}</details></section>')
navjson["agents"]=agn+[("agents-common","共同層 agents/CLAUDE.md")]
agents_html=('<p class="lede">15 個 Agent。每個資料夾含 CLAUDE.md（入口）、PERSONA.md（人設）、MANUAL.md（手冊）、USER.md、.claude/settings.json（工具白名單）、.context/（生成的規則切片）、outbox/。</p>'
 +"".join(ag)+f'<section class="agent" id="agents-common"><div class="agent-head"><span class="agent-code">共同層</span><span class="agent-model">agents/CLAUDE.md</span></div>{strip_h1(md(f"{ROOT}/agents/CLAUDE.md"))}</section>')

# Skills
sk=[];skn=[]
for s in sorted(os.listdir(f"{ROOT}/skills")):
    if not os.path.isdir(f"{ROOT}/skills/{s}"): continue
    h=strip_h1(md(f"{ROOT}/skills/{s}/SKILL.md")); h=re.sub(r'^<hr />\s*<p>name:.*?</p>\s*<hr />\s*','',h,flags=re.S)
    sid=f"skill-{s}"; skn.append((sid,s))
    sk.append(f'<section class="agent" id="{sid}"><div class="agent-head"><span class="agent-code">{s}</span></div>{h}</section>')
navjson["skills"]=skn
skills_html='<p class="lede">39 個可搬遷技能包。複製 skills/ 到 ~/.claude/skills/ 即可跨專案使用。</p>'+"".join(sk)

def cards(dept):
    return "".join(f'<a class="card" href="#agents-{a}" data-goto="agents"><div class="card-code">{META[a]["name"]}</div><div class="card-title">{META[a]["cn"]}</div><div class="card-model">{META[a]["kind"]} · {META[a]["model"]}</div></a>' for a in order if META[a]["dept"]==dept)

def box(x,y,w,h,t,s,acc=False):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="var(--surface)" stroke="{"var(--accent)" if acc else "var(--line)"}"/>'
            f'<text x="{x+w/2}" y="{y+22}" text-anchor="middle" fill="var(--text)" font-weight="600">{t}</text>'
            f'<text x="{x+w/2}" y="{y+40}" text-anchor="middle" fill="var(--muted)">{s}</text>')

know=f'''<svg viewBox="0 0 980 430" role="img" aria-label="四層知識模型">
<defs><marker id="a2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
<g font-family="var(--mono)" font-size="12">
<rect x="20" y="14" width="270" height="140" rx="6" fill="var(--surface2)" stroke="var(--accent)"/>
<text x="34" y="36" fill="var(--accent)" font-weight="600">shared/ — 單一真相</text>
<text x="34" y="58" fill="var(--muted)">CONSTITUTION.md</text><text x="34" y="76" fill="var(--muted)">PROTOCOL.md</text>
<text x="34" y="94" fill="var(--muted)">RISK_RULES.md（A 節 / G 節分開）</text><text x="34" y="112" fill="var(--muted)">METRICS · DATA · MARKETING</text>
<text x="34" y="138" fill="var(--text)">context_map.yaml 決定誰看哪幾節</text>
<line x1="290" y1="84" x2="360" y2="84" stroke="var(--accent)" marker-end="url(#a2)"/>
<text x="296" y="76" fill="var(--accent)">build_context.py</text>
<rect x="360" y="14" width="600" height="140" rx="6" fill="none" stroke="var(--line)" stroke-dasharray="4 4"/>
<text x="374" y="34" fill="var(--muted)" letter-spacing="1">生成物：agents/&lt;id&gt;/.context/（附來源 SHA-256）</text>
{box(374,46,180,50,"CHART","A 節 · 2.2 KB")}{box(566,46,180,50,"RISK","全文 · 6.7 KB")}{box(758,46,188,50,"CREATIVE","零風控條款")}
<text x="374" y="126" fill="var(--muted)">雜湊不符 → Router 不啟動、Agent 停工並 @FORGE</text>
<text x="374" y="144" fill="var(--muted)">CHART 看不到 G 節門檻 → 防 Goodhart（優化通過率而非交易品質）</text>
<rect x="20" y="180" width="940" height="110" rx="6" fill="none" stroke="var(--line)"/>
<text x="34" y="200" fill="var(--muted)" letter-spacing="1">事實知識：不進 context，用查詢 · scripts/query_readonly.py → db/002_views.sql（44 個視圖）</text>
{box(34,212,220,60,"REDTEAM","v_blind_plan：無 reasoning")}{box(266,212,220,60,"CHART","v_reject_categories：無門檻")}
{box(498,212,220,60,"CREATIVE","v_public_context：無價位")}{box(730,212,216,60,"GROWTH","只有內容與 IG 數據")}
<rect x="20" y="316" width="460" height="98" rx="6" fill="none" stroke="var(--line)"/>
<text x="34" y="336" fill="var(--muted)" letter-spacing="1">開發／運行分離（根目錄無 CLAUDE.md）</text>
{box(34,348,200,52,"dev/","你 · 開發者助理")}{box(246,348,220,52,"agents/","15 個 Agent · 憲法")}
<rect x="500" y="316" width="460" height="98" rx="6" fill="none" stroke="var(--line)"/>
<text x="514" y="336" fill="var(--muted)" letter-spacing="1">記憶三態（禁止第四態：自我修改人設）</text>
{box(514,348,140,52,"情節","session")}{box(666,348,140,52,"語意","資料倉")}{box(818,348,128,52,"程序","skills")}
</g></svg>'''

overview=f'''
<p class="eyebrow">TRADE-DESK · v3.0 · 2026-09-15 · Claude Code + Discord Router</p>
<h1 class="hero-title">多 AI Agent 量化交易 × 行銷團隊</h1>
<p class="lede">15 個 AI Agent 組成的公司，跑在一台 Windows 電腦上，只需要 Claude Pro。Blacksheep 透過 CEO 指揮全隊，從建置到營運；所有溝通走 Discord 且即時；知識用四層模型分發，做到共享一致的同時完全隔離認知。</p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">15</div><div class="kpi-l">Agent（+1 系統 Bot）</div></div>
<div class="kpi"><div class="kpi-v">39</div><div class="kpi-l">可搬遷 Skills</div></div>
<div class="kpi"><div class="kpi-v">44</div><div class="kpi-l">權限視圖</div></div>
<div class="kpi"><div class="kpi-v">70</div><div class="kpi-l">回歸測試（全通過）</div></div>
<div class="kpi"><div class="kpi-v">1.5%</div><div class="kpi-l">單筆最大損失</div></div>
</div>
<h2 id="ov-chain">指揮鏈</h2>
<p>Owner 是 <b>Blacksheep</b>，透過 <b>CEO</b> 指揮整個團隊——建置期與營運期都是。Blacksheep 只需要在 Discord 的 <code>#human-inbox</code> 跟 CEO 講話。</p>
<div class="diagram"><svg viewBox="0 0 980 210" role="img" aria-label="指揮鏈">
<defs><marker id="a3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
<g font-family="var(--mono)" font-size="12">
<rect x="20" y="20" width="200" height="56" rx="6" fill="var(--surface2)" stroke="var(--accent)"/>
<text x="120" y="44" text-anchor="middle" fill="var(--accent)" font-weight="600">Blacksheep</text>
<text x="120" y="62" text-anchor="middle" fill="var(--muted)">#human-inbox</text>
<line x1="220" y1="48" x2="290" y2="48" stroke="var(--accent)" marker-end="url(#a3)"/>
<rect x="292" y="20" width="150" height="56" rx="6" fill="var(--surface)" stroke="var(--accent)"/>
<text x="367" y="44" text-anchor="middle" fill="var(--text)" font-weight="600">CEO</text>
<text x="367" y="62" text-anchor="middle" fill="var(--muted)">單一窗口</text>
<line x1="442" y1="40" x2="512" y2="40" stroke="var(--muted)" marker-end="url(#a3)"/>
<line x1="442" y1="60" x2="512" y2="150" stroke="var(--muted)" marker-end="url(#a3)"/>
<rect x="514" y="16" width="446" height="64" rx="6" fill="none" stroke="var(--line)" stroke-dasharray="4 4"/>
<text x="528" y="34" fill="var(--muted)" letter-spacing="1">建置期 · CEO 是專案經理</text>
<text x="528" y="54" fill="var(--text)">docs/08_BUILD_PLAN.md → TASK_ASSIGN → FORGE / LAB</text>
<text x="528" y="72" fill="var(--muted)">驗收看 pytest / lint 實際輸出 · 高風險交付需 REDTEAM 審 + Blacksheep 核准</text>
<rect x="514" y="120" width="446" height="64" rx="6" fill="none" stroke="var(--line)" stroke-dasharray="4 4"/>
<text x="528" y="138" fill="var(--muted)" letter-spacing="1">營運期 · CEO 是總指揮</text>
<text x="528" y="158" fill="var(--text)">每日 08:30 總匯報 → 派工 → 審核 → HUMAN_DECISION_REQUIRED</text>
<text x="528" y="176" fill="var(--muted)">14 個 Agent 各司其職，全部走 Discord</text>
<rect x="20" y="120" width="470" height="64" rx="6" fill="none" stroke="var(--line)"/>
<text x="34" y="138" fill="var(--muted)" letter-spacing="1">無法委派的底線（Bootstrap Floor · 約 60–90 分鐘）</text>
<text x="34" y="158" fill="var(--text)">裝 Claude Code · 建 16 隻 Bot · 填金鑰 · 啟動 Router</text>
<text x="34" y="176" fill="var(--muted)">因為在 Router 跑起來之前，沒有任何 Agent 收得到訊息</text>
</g></svg></div>
<h2 id="ov-v30">v3.0：數位邊界補上 OS 層，以及 GitHub 治理</h2>
<p>v2.9 誠實承認了一件事：工具層的 allow/deny 擋不住同時擁有「寫檔」與「執行任意程式」的 Agent。
v3.0 把那個洞真正處理掉——加上 <b>L0 作業系統層沙箱</b>，並誠實標明它在 Blacksheep 的環境裡不生效。</p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">L0</div><div class="kpi-l">bubblewrap / Seatbelt：管 Bash 與其所有子程序</div></div>
<div class="kpi"><div class="kpi-v">L1</div><div class="kpi-l">settings.json allow/deny：管工具呼叫</div></div>
<div class="kpi"><div class="kpi-v">L2</div><div class="kpi-l">git worktree + merge_fix.py</div></div>
<div class="kpi"><div class="kpi-v">L3</div><div class="kpi-l">雜湊偵測 + 自動 git 還原</div></div>
</div>
<p><code>scripts/sync_sandbox.py</code> 把 <code>OWNERSHIP.yaml</code> 的 <code>writable_paths</code>
翻成 15 份沙箱設定（lint 第 21 項驗證同步）。過程中抓到一個真漏洞：
CHART 在工具層被 deny 讀 <code>RISK_RULES.md</code>（Goodhart 防護），
卻一直可以用 Bash <code>cat</code> 讀到——現在每一條 <code>Read</code> deny 都自動鏡射成沙箱的 <code>denyRead</code>。</p>
<p><b>Blacksheep 跑原生 Windows，所以 L0 不存在</b>（Claude Code 的沙箱只支援 macOS / Linux / WSL2）。
預設 <code>TD_REQUIRE_SANDBOX=0</code>，隔離是 L1 + L2 + L3：
FORGE / LAB 的逃逸路徑<b>擋不住，但 30 秒內被抓到、自動 <code>git checkout</code> 還原、HALT 並 @你</b>。
Router 啟動時會把這件事大聲印出來——最糟的失效模式是「以為有沙箱」。
真正會虧錢的三條路徑（下單、寫資料倉、改風控）本來就不靠 L0 守，全部是程式在把關。</p>
<h3>GitHub：要用，但只用三件事</h3>
<p>版本歷史與回滾、Actions 當唯一的 reviewer、<code>git tag</code> 標記實盤版本。
查證後確認：<b>Free 方案的私有庫沒有分支保護、也沒有 secret scanning</b>，
所以伺服器端擋不住任何東西，防線必須在本機——
<code>check_secrets.py</code>（自製 push protection，含全歷史掃描）＋
<code>install_git_hooks.py</code>（pre-commit / pre-push）＋
<code>backup_mirror.py</code>（3-2-1 備份，GitHub 是遠端副本不是備份）。</p>
<h2 id="ov-guarantee">v2.9：四個保證，各自由一支程式驗證</h2>
<p>「不重疊、無縫、不混淆、不越權」寫在文件裡只是願望。每一條現在都對應一支 Router 啟動時會執行的程式：</p>
<table><thead><tr><th>保證</th><th>單一真相</th><th>驗證者</th><th>驗到什麼</th></tr></thead><tbody>
<tr><td><b>職責不重疊</b></td><td><code>shared/OWNERSHIP.yaml</code>：34 項責任各一個 owner</td><td><code>verify_isolation.py</code>（lint 19）</td><td>owner 存在；<b>別人的手冊職責段不得出現你的責任</b></td></tr>
<tr><td><b>交接無縫</b></td><td>PROTOCOL 的 msg_type 表 + 15 條關鍵交接</td><td><code>sync_manual_msgflow.py</code>（lint 17）</td><td>產出者與接收者<b>雙方手冊都寫了</b>——曾有 35 條鏈只有單邊</td></tr>
<tr><td><b>角色不混淆</b></td><td>各 PERSONA 的「與相近角色的界線」句</td><td><code>verify_isolation.py</code></td><td>十個易混淆角色都有界線句；Router 每次呼叫重貼角色提醒</td></tr>
<tr><td><b>權限隔離</b></td><td>OWNERSHIP 的 <code>writable_paths</code></td><td><code>verify_isolation.py</code> + <code>guard_paths.py</code></td><td>寫入權對得上 owner；<b>並主動列出逃逸路徑</b></td></tr>
<tr><td><b>共同認知</b></td><td><code>shared/MISSION.md</code></td><td>lint 20</td><td>15 份逐字一致——任一份不同＝團隊對目標的認知已分岐</td></tr>
</tbody></table>
<h3>我找到的真問題：工具層擋不住有執行權的 Agent</h3>
<p><code>verify_isolation.py --escapes</code> 會直接印出來，因為這不該被隱瞞：</p>
<pre><code>⚠️ 工具層逃逸路徑
  - forge：寫入 Write(worktree/**)       執行 Bash(python worktree/*)
  - lab  ：寫入 Write(../../backtest/**) 執行 Bash(python ../../backtest/*)</code></pre>
<p>FORGE 要寫程式、LAB 要寫回測，<b>這個組合是設計上必要的</b>，拿掉它們就沒法工作。所以隔離是三層：</p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">L1 工具層</div><div class="kpi-l">15 份 settings.json 的 deny 基線（lint 14）</div></div>
<div class="kpi"><div class="kpi-v">L2 沙箱</div><div class="kpi-l">FORGE 只能寫 worktree；合併只能由 merge_fix.py</div></div>
<div class="kpi"><div class="kpi-v">L3 偵測</div><div class="kpi-l">每次呼叫後比對 201 個檔案，未授權變更自動還原</div></div>
</div>
<p><b>L3 是偵測 + 自動回滾，不是預防。</b> 真正的預防需要 OS 層 ACL（每個 Agent 一個 Windows 帳號），
代價是 15 份 Claude Code 登入與額度分裂——目前判定不值得，但<b>這是判斷不是事實</b>，若哪天管理他人資金就該重做。</p>
<p>實測過：讓 LAB 去改 CHART 的手冊與 <code>RISK_RULES.md</code>，守衛在下一次呼叫結束時抓到並還原。</p>
<h2 id="ov-review">v2.8：白皮書框架與 Agent 邊界稽核</h2>
<p>這一版做了兩次獨立稽核——一次針對白皮書作為<b>文件</b>的完整性，一次針對 15 個 Agent 的<b>職責邊界</b>。</p>
<h3>一、白皮書缺的思考</h3>
<table><thead><tr><th>缺什麼</th><th>為什麼重要</th></tr></thead><tbody>
<tr><td><b>沒有問題陳述</b>——全文從解法開始</td><td>沒有「要解決什麼」，任何機制都沒有評判標準。新增 §0.0：五個手動交易的失效模式，各自對應到哪個機制；<b>對應不上的機制就該砍掉</b></td></tr>
<tr><td><b>沒有經濟學</b>——一個成本數字都沒有</td><td>交易系統白皮書最刺眼的缺口。新增 §11.5：固定/變動成本、月交易筆數、<b>最小可運作帳戶規模</b>（隱含在 B 節 <code>qty &lt; min_qty</code> 卻從未被算出來）</td></tr>
<tr><td><b>沒有論證 LLM 加值</b></td><td>「LLM 提案、程式執行」是鐵律，但系統每一道關卡都是程式。新增 §2.2b：只有四件事程式做不到，並要求第 8 週<b>同時跑純規則基準線——贏不過就砍掉 LLM 提案層</b></td></tr>
<tr><td><b>沒有威脅模型</b></td><td>每天讀外部網頁、單一 Discord 帳號授權金錢操作。新增 §7.2：五個攻擊者，每個都寫「沒防住的部分」</td></tr>
<tr><td><b>沒有終止條件</b></td><td>只有「進入真錢的門檻」，沒有「什麼時候該收攤」。新增 §14.3 五條，並要求 CEO 主動提出</td></tr>
</tbody></table>
<h3>二、一個數學問題：½ Kelly 其實不生效</h3>
<p>代入實際參數：<code>p=0.40, RR=2 → kelly_f=0.10 → ½Kelly=5.0%</code>，被 1.5% 上限截斷。<b>只有勝率低於 35.4%，Kelly 才會真正生效。</b></p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">35.4%</div><div class="kpi-l">½ Kelly 開始咬合的勝率門檻</div></div>
<div class="kpi"><div class="kpi-v">1.5%</div><div class="kpi-l">實際生效的風險上限（幾乎總是它）</div></div>
<div class="kpi"><div class="kpi-v">保險絲</div><div class="kpi-l">Kelly 的真實角色，不是放大器</div></div>
</div>
<p>系統實際跑的是「固定 1.5% 風險 + 低勝率保險絲」。<b>這是對的，但必須寫清楚</b>——否則讀者與每天讀規則的 Agent 會以為績效好時部位會放大。</p>
<h3>三、Agent 邊界的問題</h3>
<table><thead><tr><th>問題</th><th>後果</th></tr></thead><tbody>
<tr><td>FEED 與 LEDGER 對同一條 SUSPECT 規則各判一次</td><td>append-only 表會出現兩筆互相矛盾的標記，且無仲裁者</td></tr>
<tr><td><b>AUDIT 被授權「停用 setup」卻沒有管道能落地</b></td><td>優化循環的 L2 處置永遠無法執行，且抵觸憲法三</td></tr>
<tr><td><b>季審七步中第 1、6 步沒有排程</b></td><td>LAB 要回測的假設從未被產出；<b>RISK 的最後風險關卡從未被叫醒</b></td></tr>
<tr><td><b>35 個 msg_type 交接破口</b></td><td><code>REGIME_REPORT</code> 兩端手冊都沒寫、<code>RECONCILE_ALERT</code> 沒有收件方</td></tr>
<tr><td><b><code>.context/optimize.md</code> 生成了卻沒有 @import</b></td><td>整個優化循環從未進入任何 Agent 的 context</td></tr>
<tr><td><b>CHART 能直接讀 <code>shared/RISK_RULES.md</code></b></td><td>Goodhart 防護是紙做的——15 份手冊還逐字指示它去讀原檔</td></tr>
<tr><td>KPI 自報（EXEC、AUDIT、WATCH、CEO）</td><td>違反憲法第八條。<code>METRICS_SPEC</code> §7 寫死外部量測者；AUDIT 與 WATCH 互相量測</td></tr>
<tr><td>15 份人設逐字重複憲法，佔約四成篇幅</td><td>其中 FORGE 那份寫著「發 BUG_REPORT 給 FORGE」＝向自己報修</td></tr>
<tr><td><b>我上一版造成的兩個新問題</b></td><td>deny 基線把 FORGE 也擋住（它正是手冊的維護者）；季審在手冊裡被渲染成「每月 6 日」</td></tr>
</tbody></table>
<p>新增 <code>sync_manual_msgflow.py</code> 與 lint 第 17、18 項，讓這兩類破口不會再回來。</p>
<h2 id="ov-audit">v2.7：一致性稽核的結果</h2>
<p>這一版做了一次完整的文件 vs repo 稽核。<b>找到的問題比預期多，而且有幾個會直接誤導 Agent</b>：</p>
<table><thead><tr><th>問題</th><th>後果</th><th>處置</th></tr></thead><tbody>
<tr><td>白皮書寫 Risk Gate 檢查 <code>A1–A12</code></td><td>實際是 A1–A8（提案要件）+ G1–G15（Gate 門檻），兩套編號被混用</td><td>全部改正</td></tr>
<tr><td>MACRO 的切片寫著「你的事件日曆會被 RISK 的 A7/A11/A14 使用」</td><td><b>這三個條款不存在</b>，而 MACRO 每次啟動都會讀到</td><td>改為 G7/G8/G14</td></tr>
<tr><td><code>stop_reason</code> 的 <code>SESSION_LIQUIDITY</code> 不在 schema enum 裡</td><td>AUDIT 照手冊產出的 TRADE_REVIEW 會被驗證擋下</td><td>補進 schema</td></tr>
<tr><td>EXEC 的棘輪與對帳「每 5 分鐘」</td><td><b>scheduler.yaml 裡 exec 一個 job 都沒有</b>——止損棘輪沒有任何觸發來源</td><td>補 exec-ratchet / exec-reconcile + lint 第 16 項</td></tr>
<tr><td><code>!approve</code> 掛在 CEO（LLM）身上</td><td>你打 <code>!approve</code>，LLM 說「已核准」，<b>系統狀態一個位元都沒變</b></td><td>改掛 WATCH 的 apply_change.py</td></tr>
<tr><td>切片只驗來源、不驗產物，且 <code>.context/</code> 在 gitignore 內</td><td>直接改 <code>chart/.context/rules.md</code> 不會被發現——隔離的地基是空心的</td><td>MANIFEST 存輸出雜湊；全體 deny <code>Write(.context/**)</code></td></tr>
<tr><td>數字漂移：41 個視圖（實際 44）、8 項 lint（實際 16）、35 個排程（實際 43）、七條鐵律（實際 9）</td><td>照文件驗收的人會得到錯的結論</td><td>新增 <code>verify_docs_claims.py</code>，變成 lint 第 15 項</td></tr>
<tr><td><code>router/.env.example</code> 根本不存在</td><td>bootstrap 第 7 步 <code>Copy-Item</code> 必定失敗，而那一步在 Router 啟動前、沒有 Agent 能幫你</td><td>補上完整範本</td></tr>
</tbody></table>
<div class="kpis">
<div class="kpi"><div class="kpi-v">16</div><div class="kpi-l">lint 檢查項（新增 14/15/16）</div></div>
<div class="kpi"><div class="kpi-v">38</div><div class="kpi-l">回歸測試</div></div>
<div class="kpi"><div class="kpi-v">0</div><div class="kpi-l">文件與 repo 不一致處</div></div>
</div>
<h2 id="ov-gov">v2.7：治理層（版控 · 備份 · 汙染防治）</h2>
<p><b>AI 每天在改這個 code base，所以保護 code base 本身的那一層必須先存在。</b></p>
<table><thead><tr><th>面向</th><th>機制</th></tr></thead><tbody>
<tr><td>分支與合併</td><td><code>main</code> 是 Router 正在跑的程式；FORGE/LAB 只能開 <code>fix/*</code>、<code>feat/*</code>，settings deny 了 <code>git push</code>／<code>reset</code>／<code>checkout main</code>。合併只有 <code>merge_fix.py</code>（verify → build_context → lint → pytest → merge → 觸發重啟）</td></tr>
<tr><td>Tag 與回滾</td><td><code>params-v&lt;n&gt;</code> 對應 <code>config_versions</code>；回滾條件明訂。<b>資料庫不回滾</b>，錯誤資料用 <code>corrections</code> 表更正</td></tr>
<tr><td>備份三層</td><td>L1 git + 私有 remote／L2 <code>.backup</code> API + Parquet（第二顆磁碟 + 雲端，90 天）／L3 金鑰加密離線。<b>演練過一次完整還原才准上真錢</b></td></tr>
<tr><td>汙染防治</td><td>開發與 Agent 是兄弟目錄、根目錄無 CLAUDE.md；切片有輸出雜湊；<code>~/.claude/skills/</code>、<code>.venv/</code>、user-scope MCP 三個共享狀態各有處置</td></tr>
<tr><td>金鑰</td><td>七類憑證的效期、徵兆、負責提醒的 Agent；每 90 天輪換；外洩止血四步</td></tr>
</tbody></table>
<p>災難情境也補完了：斷電重開機（<b>開機先 <code>executor.py recover</code> 對帳補止損再啟動</b>）、Discord 中斷（自動 NO_NEW_ENTRY + 離線平倉出口）、資料庫損壞五步、Router 崩潰迴圈。並新增 <code>system_state.trading</code> 狀態機與<b>繞過 CEO 的直達清單</b>——CEO 是唯一沒有獨立監督的角色，訊號必須有第二條路到達人。</p>
<h2 id="ov-multi">v2.7：多專案資產複用</h2>
<p><code>legacy/projects.yaml</code> 登錄多個舊專案 → <code>scan_legacy.py --all</code> 產出索引與<b>能力對照表</b>。同一種能力有多個候選時，依 <code>trust</code> 與「已驗證的事實」選一個——<b>不要合併兩個專案的同一種能力</b>，那會同時繼承兩邊的假設。</p>
<p>另外還有一半是程式掃不到的：<b>經驗</b>。第一週請 CEO 用五個問題問你（最讓你意外的是什麼？後悔的決定？不敢動的程式？真正花掉最多時間的？已知但沒修的問題？），答案寫進各專案的 <code>known_issues</code>，並<b>轉成新程式的測試案例</b>——繼承一個舊 bug 而不知道它存在，是移植最貴的失敗方式。</p>
<h2 id="ov-opt">v2.6：策略優化循環（1–3 個月一輪）</h2>
<p><b>策略不會自己變好，也不該天天被改。</b> 核心原則：<b>診斷可以隨時做，處方只在固定時點開。</b></p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">L1 / L2 / L3</div><div class="kpi-l">週檢視 · 月審 · 季審</div></div>
<div class="kpi"><div class="kpi-v">±20% → 70%</div><div class="kpi-l">參數高原檢定（擾動後仍需保有的 expectancy）</div></div>
<div class="kpi"><div class="kpi-v">½ Kelly</div><div class="kpi-l">與 1.5% 上限取小</div></div>
</div>
<table><thead><tr><th>層級</th><th>頻率</th><th>主責</th><th>能改什麼</th><th>核准</th></tr></thead><tbody>
<tr><td>L1 週檢視</td><td>每週</td><td>AUDIT</td><td><b>什麼都不能改</b>，只產出假設清單</td><td>—</td></tr>
<tr><td>L2 月審</td><td>每月 1 號</td><td>AUDIT + RISK</td><td>只能改統計量（kelly_p）與<b>停用</b> setup</td><td>CEO 覆核</td></tr>
<tr><td>L3 季審</td><td>1/4/7/10 月</td><td>LAB 主導</td><td>參數本體：止損 ATR、min_rr、型態門檻、setup 定義</td><td>REDTEAM → RISK → <b>你 !approve</b></td></tr>
</tbody></table>
<p>這同時防兩種失敗：<b>過度反應</b>（連虧三筆就改參數，把雜訊當訊號）與<b>完全不動</b>（regime 換了半年還在跑舊假設）。季審<b>強制執行</b>，「維持現狀」是合法結論，但必須是跑完流程後的結論。</p>
<p><b>參數高原</b>是防過度擬合的主要工具：把參數上下移動 20%，expectancy 必須仍保有 70%。做不到就代表這個值是曲線擬合出來的——<b>即使回測數字最好也不採用</b>，改用高原中心值。這是為什麼季審叫「重新擬合」而不是「重新最佳化」。</p>
<h2 id="ov-patterns">v2.6：型態學與 MSS</h2>
<p>型態學與 SMC <b>並用而非二選一</b>：型態給形狀與目標，SMC 給流動性與誰被套；兩者指向同一價位才是高信心（只有型態、無 SMC 依據時信心上限 0.6）。突破必須通過<b>量價確認</b>（≥ 前 20 根均量 × 1.5），否則視為假突破不提案——這是型態學最常見的虧損來源。</p>
<p><b>MSS（市場結構轉變）</b>：CHoCH 只是警訊，MSS 才是已確認的轉變（收盤站穩被破壞結構點外 ≥ 0.25 ATR、且 12 根內回測不破）。<code>htf_bias</code> 只在 MSS 成立時翻轉，不因單根 CHoCH 翻向。</p>
<h2 id="ov-legacy">v2.6：既有專案資產複用</h2>
<p>你在別的專案已經做出可用的 K 線採集、策略、戰情室、Bitget 串接、Canva、Tailscale、Notion 推送。流程刻意不是「把舊專案丟給 Agent 讀」：</p>
<p><code>scan_legacy.py 盤點</code> → <code>docs/11_LEGACY_ASSETS.md</code>（你標 PORT/REF/SKIP）→ CEO 逐項派工 → FORGE 用 <code>legacy-port</code> skill <b>只讀被指派的檔</b>。理由有兩個：舊專案的規則與假設會污染新 Agent 的 context；整包讀會讓 token 爆量。移植時強制拆開三層分離（分析／風控／執行）並清掉硬編碼金鑰。</p>
<h2 id="ov-boundary">v2.5：交易日邊界（台北 08:00）</h2>
<p><b>台北 08:00 = 00:00 UTC。</b> 這一刻日 K 收線（週一同時收週 K、1 號同時收月 K）、<code>RISK_RULES</code> C1 的單日虧損計數重置、所有報表的「昨日／本月」換日。系統所有時間定義以此為準。</p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">08:00</div><div class="kpi-l">交易日邊界（台北）＝ 00:00 UTC</div></div>
<div class="kpi"><div class="kpi-v">8.2 → 6.0</div><div class="kpi-l">最壞情況 5 小時窗（月報 × 週日疊加）</div></div>
<div class="kpi"><div class="kpi-v">13</div><div class="kpi-l">lint 檢查項（新增手冊排程一致性）</div></div>
</div>
<p><b>我修掉了自己造成的一個 correctness 錯誤。</b> v2.4 為了平衡額度把「昨日日報」移到 05:30——那在交易日結束<b>之前</b>，報的是不完整的一天。原則現在寫進排程表檔頭：<b>排程可以為額度挪動，但不能跨過交易日邊界。</b></p>
<table><thead><tr><th>時間</th><th>任務</th><th>為什麼是這個順序</th></tr></thead><tbody>
<tr><td>08:01 / 08:03</td><td>FEED 採集 → 指標</td><td>收線後第一根完整日 K 落庫，指標才算得準</td></tr>
<tr><td>08:08</td><td>CHART 高時框（opus）</td><td>前面掛 <code>daily_close_check.py</code>：日／週／月 K 與指標都到位才叫醒 opus</td></tr>
<tr><td>08:20</td><td>AUDIT 昨日日報</td><td>交易日已結算，才算得出「昨日」</td></tr>
<tr><td>08:35</td><td>CEO 每日匯報</td><td>彙整前面三份產物</td></tr>
<tr><td>08:40</td><td>CHART 重試</td><td>08:08 因資料未到位 SKIP 時補跑；<code>mutex_with</code> 標記，額度只計一次</td></tr>
</tbody></table>
<p><b>兩個新的守門機制</b>：<br>
① <b>lint 第 12 項改算最壞情況</b>——任何「幾號」都可能落在任何星期幾，改以「每日 × 該星期 × 該號」三者疊加驗證。這揪出了原本漏掉的重疊（週日晚間最高 8.2）。<br>
② <b>lint 第 13 項：手冊排程行必須與 <code>scheduler.yaml</code> 一致</b>，由 <code>sync_manual_cron.py</code> 生成。先前 15 份手冊的時間是手抄的，早就漂掉了（手冊寫 <code>redteam-htf-review 08:15</code>，實際是 13:30）——Agent 讀到的是錯的。排程表現在是單一真相。</p>
<h2 id="ov-load">v2.4：排程負載平衡</h2>
<p>Claude Pro 是 <b>5 小時滾動窗</b>，會痛的是「爆量」不是「總量」。原本的排程有三個擠壓點，重排後全年每一天的峰值都壓到 6.0。</p>
<div class="kpis">
<div class="kpi"><div class="kpi-v">19.0 → 6.0</div><div class="kpi-l">全年最差 5 小時窗權重</div></div>
<div class="kpi"><div class="kpi-v">4</div><div class="kpi-l">opus 任務（彼此間隔 ≥ 5 小時）</div></div>
<div class="kpi"><div class="kpi-v">R1–R5</div><div class="kpi-l">排程規則（lint 會擋回歸）</div></div>
</div>
<table><thead><tr><th>時段</th><th>原本</th><th>重排後</th></tr></thead><tbody>
<tr><td>每日早晨</td><td>07:30–09:00 六個任務、<b>三個 opus 擠在 90 分鐘</b>，權重 12.0</td><td>redteam 移到 13:30、creative 移到 15:00 → 6.0（audit 曾被移到 05:30，v2.5 修正回 08:20）</td></tr>
<tr><td>週報</td><td>週日 18:00–20:30 九個任務全擠一起</td><td>拆到週六（audit / lab / risk）與週日（growth / cmo / watch / 週會）</td></tr>
<tr><td>月報</td><td>1 號 08:00–12:00 五個月報疊在每日群上，權重 19.0</td><td>拆到 1–5 號，且避開早晨窗（v2.5 再定為 23:50 / 02:10）</td></tr>
<tr><td>CEO 每日匯報</td><td>opus</td><td><b>降為 sonnet</b>；opus 改用在週日週會（彙整不需要 opus，深度判斷才需要）</td></tr>
</tbody></table>
<p><b>評估過但未採用</b>：把輕量 Agent 搬到本地 LLM。實測 RTX 3070 8GB 可跑 8B（73 tok/s、5.4GB），但額度是被 CHART／REDTEAM／FORGE／LAB 吃掉的，那四個都不能本地化；能搬的只佔 10–15%，換一週工程與一個新故障點不划算。排程重排達到同樣目的，成本接近零。</p>
<h2 id="ov-harness">v2.3：內化外部實戰經驗</h2>
<p>對照一位 AI Agent 開發者的五篇實戰文章逐條檢查。<b>其中一項是我們程式裡真的存在的 bug</b>。完整分析與「刻意不採納」的理由見「Harness」分頁。</p>
<table><thead><tr><th>他踩過的坑</th><th>我們原本</th><th>處置</th></tr></thead><tbody>
<tr><td>缺少終止條件是多 Agent 失敗主因（41.8%）</td><td><b>真 bug</b>：hop 靠 LLM 自報，沒寫就重置為 0</td><td>Router 自己記帳；另加 a2a 5 輪上限</td></tr>
<tr><td>Agent 對客套話無限回應</td><td>沒有沉默機制</td><td><code>NO_REPLY</code> → 💤 不貼訊息</td></tr>
<tr><td>「不能讓一個人自己幫自己打分數」</td><td>CEO 看 FORGE <b>自報</b>的測試結果</td><td><code>verify_delivery.py</code> 由審核者自己跑</td></tr>
<tr><td>未驗證知識污染下游</td><td>教訓直接進資料倉，無成熟度標記</td><td>UNVERIFIED → VALIDATED → PROMOTED，隔離做在視圖層</td></tr>
<tr><td>Skill 塞五件事 → 無法歸因失敗</td><td>3 個 skill 混了 4–5 件事</td><td>拆成 8 個；36 個技能全部補上 I/O 契約</td></tr>
<tr><td>權限缺失造成靜默失敗（debug 兩小時）</td><td>沒有檢查</td><td>開機檢查 16 隻 Bot × 9 項權限，缺就拒絕啟動</td></tr>
<tr><td>每小時建 thread 會塞爆頻道</td><td>封存時間寫死 1440</td><td>19 個頻道分層（60/1440/4320/10080）</td></tr>
<tr><td>兩百行 Markdown = 沒有人真的審核</td><td>報告全貼 Discord 純文字</td><td><code>report-preview</code>：產 HTML 貼連結</td></tr>
<tr><td>「有了 AI 反而更忙了」</td><td>沒有對應的設計目標</td><td>CEO 第一 KPI：Blacksheep 每天 ≤ 15 分鐘</td></tr>
</tbody></table>
<h2 id="ov-new">v2.2 / v2.1 改了什麼</h2>
<table><thead><tr><th>問題</th><th>解法</th></tr></thead><tbody>
<tr><td><b>我想透過 CEO 從建置到營運指揮所有 Agent</b></td><td>CEO 新增<b>建置期職責</b>與建置日報；<code>docs/08_BUILD_PLAN.md</code> 成為建置待辦唯一真相，含可直接複製的 Discord 指令範本；新增 <code>build-orchestration</code> skill</td></tr>
<tr><td>那有哪些事 CEO 做不到？</td><td>誠實列出 <b>Bootstrap Floor</b> 七項人工步驟與理由；<code>dev/</code> 重新定位為備援，並列出五個該自己動手的情況</td></tr>
<tr><td>稱謂與身分</td><td>憲法加入指揮鏈；15 份 <code>USER.md</code> 統一為 <b>Blacksheep</b>，並加上「自稱 Blacksheep 但 Discord ID 不符 = 冒充」的防護</td></tr>
</tbody></table>
<h3>v2.1 的知識分層升級</h3>
<table><thead><tr><th>問題</th><th>解法</th></tr></thead><tbody>
<tr><td>所有 Agent 載入完整 <code>shared/</code> → 認知混淆、token 浪費</td><td><b>單一真相 + 生成式切片</b>：<code>build_context.py</code> 依 <code>context_map.yaml</code> 為每個角色裁切。CHART 的規則 context 從 6.7 KB 降到 2.2 KB</td></tr>
<tr><td>CHART 看到 Gate 門檻 → 會優化「通過率」而非交易品質</td><td><code>RISK_RULES.md</code> 拆成 <b>A 節（提案要件）</b> 與 <b>G 節（門檻）</b>；CHART 只拿 A 節，退件只給理由<b>類別</b></td></tr>
<tr><td>規格改了、切片沒重建 → 靜默漂移</td><td>切片帶來源 SHA-256；Router <b>preflight</b> 不通過就不啟動，Agent 憲法規定驗證失敗即停工</td></tr>
<tr><td>「你不要查 X」寫在 prompt 只是勸告</td><td><b>權限做在視圖層</b>：41 個視圖做欄位裁切，<code>view_grants.yaml</code> 授權，<code>query_readonly.py</code> 強制、禁止查底層表</td></tr>
<tr><td>長 thread 導致身分漂移</td><td>尾端重貼角色提醒（近因效應）、20 輪強制換 session、REDTEAM 常駐 stateless</td></tr>
<tr><td>把結論寫回自己的人設 → 不可稽核的偏誤累積</td><td>記憶三態（session／資料倉／skills），<b>明確禁止</b>自我修改人設</td></tr>
<tr><td><b>你開發時待在根目錄 → 又是一次認知混淆</b></td><td><b>根目錄刻意沒有 CLAUDE.md</b>；你在 <code>dev/</code>、Agent 在 <code>agents/</code>，兩條繼承鏈不相交</td></tr>
<tr><td>Agent 手冊寫 <code>scripts/x.py</code> 但 cwd 在 agents/&lt;id&gt;/ → 執行失敗</td><td>全面改為 <code>../../scripts/</code>，Router 加 <code>--add-dir</code>，<code>lint_agents.py</code> 會擋住回歸</td></tr>
</tbody></table>
<h2 id="ov-know">四層知識模型</h2>
<div class="diagram">{know}</div>
<h2 id="ov-tree">專案結構</h2>
<pre><code>trade-desk/
├── docs/          白皮書 · 架構 · 教學 · <b>開發環境</b> · 維運 · 路線圖 · 術語 · adr/
├── shared/        ★ 單一真相：憲法 · 協定 · 風控 · 量尺 · Schema · 參數 · 切片與權限設定
├── agents/        CLAUDE.md（共同層）+ 15 個 Agent（人設 · 手冊 · .context/ 切片 · outbox/）
├── skills/        30 個可搬遷技能包
├── router/        discord_router.py · agents.yaml · scheduler.yaml · watchdog.ps1
├── engine/        核心程式：唯一碰錢與寫資料的地方（待實作，README 有規格與驗收）
├── scripts/       build_context · lint_agents · query_readonly · init_db（已實作）+ 待實作清單
├── db/            001_schema.sql（31 表）· 002_views.sql（41 權限視圖）
├── backtest/ dashboard/ marketing/ data/ logs/ tests/
└── dev/           ★ 你的開發工作區 ← cd 到這裡開 Claude Code
</code></pre>
<p>每個資料夾都有 <code>README.md</code> 說明該放什麼、每支程式的規格與驗收標準。</p>
<h2 id="ov-team">團隊</h2>
<h3>指揮</h3><div class="cards">{cards("指揮")}</div>
<h3>交易</h3><div class="cards">{cards("交易")}</div>
<h3>工程</h3><div class="cards">{cards("工程")}</div>
<h3>行銷</h3><div class="cards">{cards("行銷")}</div>
<h2 id="ov-start">怎麼開始</h2>
<ol class="flow">
<li>解壓 <code>trade-desk.zip</code> 到 <code>C:\\trade-desk</code></li>
<li><code>python scripts\\build_context.py</code> → <code>init_db.py</code> → <code>lint_agents.py</code>（應顯示「通過」）</li>
<li>照 <b>QUICKSTART.md</b> 建 2 隻 Bot，讓 CEO 在 Discord 回你一句話</li>
<li>照 <code>docs/03_DISCORD_SETUP.md</code> 建完其餘 14 隻</li>
<li><code>cd dev</code> 開 Claude Code，照 <code>TASKS.md</code> 的 P0 開始實作</li>
</ol>
'''
navjson["overview"]=[("ov-chain","指揮鏈"),("ov-v30","v3.0 邊界與 GitHub"),("ov-guarantee","v2.9 四個保證"),("ov-review","v2.8 框架與邊界稽核"),("ov-audit","v2.7 一致性稽核"),("ov-gov","v2.7 治理層"),("ov-multi","v2.7 多專案複用"),("ov-opt","v2.6 優化循環"),("ov-patterns","v2.6 型態學/MSS"),("ov-legacy","v2.6 資產複用"),("ov-boundary","v2.5 交易日邊界"),("ov-load","v2.4 排程平衡"),("ov-harness","v2.3 經驗內化"),("ov-new","v2.2 / v2.1 改了什麼"),("ov-know","四層知識模型"),("ov-tree","專案結構"),("ov-team","團隊"),("ov-start","怎麼開始")]

tabs=[("overview","總覽"),("wp","白皮書"),("arch","架構"),("build","建置流程"),("bound","邊界"),("github","GitHub"),("harness","Harness"),("devenv","開發環境"),("agents","Agent"),("skills","Skills"),("spec","規格"),("router","Router"),("setup","教學"),("ops","維運"),("roadmap","路線圖"),("adr","ADR"),("glossary","術語")]
tab_html="".join(f'<button class="tab" data-tab="{d}">{l}</button>' for d,l in tabs)
pmap={d:h for d,l,h in panels}
panel_html="".join(f'<div class="panel" data-panel="{d}">{ {"overview":overview,"agents":agents_html,"skills":skills_html,"spec":spec_html,"router":router_html,"adr":adr_html}.get(d, pmap.get(d,"")) }</div>' for d,l in tabs)
css=open(f"{ROOT}/docs/site.css", encoding="utf-8").read()
css+="\n.ctxline{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:0 0 8px;padding:4px 8px;background:var(--code);border-radius:3px;display:inline-block}\n"
LAB={"overview":"總覽","wp":"白皮書章節","arch":"架構","build":"建置流程","bound":"四層邊界","github":"版控與備份","harness":"經驗內化","devenv":"開發環境","agents":"Agent","skills":"Skills","spec":"規格文件","router":"程式","setup":"教學步驟","ops":"維運","roadmap":"里程碑","adr":"決策紀錄","glossary":"術語"}
page=f'''<title>TRADE-DESK 白皮書</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>{css}</style>
<div class="top"><span class="brand">TRADE-DESK v3.0</span>{tab_html}</div>
<div class="wrap"><nav class="side" id="side"></nav><main id="main">{panel_html}</main></div>
<script>
const NAV={json.dumps(navjson,ensure_ascii=False)},LABELS={json.dumps(LAB,ensure_ascii=False)};
const tabs=[...document.querySelectorAll('.tab')],panels=[...document.querySelectorAll('.panel')],side=document.getElementById('side');
function show(id,anchor){{tabs.forEach(t=>t.classList.toggle('active',t.dataset.tab===id));panels.forEach(p=>p.classList.toggle('active',p.dataset.panel===id));
 side.innerHTML='<div class="lab">'+(LABELS[id]||id)+'</div>'+(NAV[id]||[]).map(([s,t])=>'<a href="#'+s+'" data-s="'+s+'">'+t+'</a>').join('');
 try{{localStorage.setItem('td-tab',id)}}catch(e){{}}
 if(anchor){{const el=document.getElementById(anchor);if(el)el.scrollIntoView({{block:'start'}});}}else window.scrollTo(0,0);spy();}}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.tab)));
document.addEventListener('click',e=>{{const a=e.target.closest('a[data-goto]');if(a){{e.preventDefault();show(a.dataset.goto,a.getAttribute('href').slice(1));}}}});
function spy(){{const p=document.querySelector('.panel.active');if(!p)return;const hs=[...p.querySelectorAll('h2[id],section[id]')];let cur=hs[0];for(const h of hs){{if(h.getBoundingClientRect().top<120)cur=h;}}
 side.querySelectorAll('a').forEach(a=>a.classList.toggle('cur',cur&&a.dataset.s===cur.id));}}
document.addEventListener('scroll',spy,{{passive:true}});
let init='overview';try{{init=localStorage.getItem('td-tab')||'overview'}}catch(e){{}}
const h=location.hash.slice(1);if(h){{const pid=Object.keys(NAV).find(k=>NAV[k].some(([s])=>s===h));if(pid)init=pid;}}
if(!NAV[init])init='overview';show(init,h||null);
</script>'''
open(OUT,"w",encoding="utf-8").write(page)
print(f"已產生 {OUT}（{len(page)/1024:.0f} KB，{len(tabs)} 個分頁）")
