"""實跑 Router 的 handle()——用假的 Discord 物件，不連網、不呼叫 claude。

為什麼需要這一份：
    v3.0.10 之前，`handle()` 這條路徑**從來沒有被執行過**：
    排程被一層同步 lambda 擋在執行緒裡（RuntimeError），
    worker 又沒有 except，一有例外就永久消失且不出聲。
    兩個都修好之後，第一個真正跑到的 Agent 立刻炸在 `handle()` 的**第一行**：

        msg._agent = aid
        AttributeError: 'Message' object has no attribute '_agent'
                        and no __dict__ for setting new attributes

    ——`discord.Message` 有 `__slots__`。這種 bug 只要跑過一次就會現形，
    所以這份測試的重點不是斷言細節，而是**真的把整條路徑跑一遍**。

    假的 Message 也故意加上 `__slots__`，讓「往別人的物件掛屬性」這類寫法
    在 CI 就死，而不是在 Blacksheep 的 Discord 上死。
"""
from __future__ import annotations

import asyncio
import importlib.util
import itertools
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


# ── 假的 Discord 物件 ────────────────────────────────────────────
class FakeUser:
    def __init__(self, uid, bot=False, name="user"):
        self.id, self.bot, self.name = uid, bot, name


# 每個頻道一個新 id。Router 用 channel.id 當 thread_id 記「鏈的跳數」，
# 固定 id 會讓前一個測試留下的跳數累加到下一個測試，直到撞上 max_hops——
# 測試單獨跑會過、整份跑會掛，這種假失敗比真 bug 還難查。
_CID = itertools.count(100_000)


class FakeChannel:
    def __init__(self, cid=None):
        self.id = next(_CID) if cid is None else cid
        self.sent: list[str] = []

    async def send(self, content=None, **kw):
        self.sent.append(content or "")
        return FakeMessage(content or "", channel=self)

    async def create_thread(self, **kw):
        return FakeThread()

    def history(self, limit=20):
        async def _gen():
            for _ in ():
                yield None
        return _gen()


class FakeThread(FakeChannel):
    pass


class FakeGuild:
    def __init__(self, gid):
        self.id = gid
        self.me = FakeUser(9001, bot=True, name="me")


class FakeMessage:
    """故意用 __slots__——真的 discord.Message 就是這樣，往上掛屬性會 AttributeError。"""
    __slots__ = ("content", "author", "channel", "guild", "id", "mentions",
                 "jump_url", "reactions", "replies")

    def __init__(self, content, author=None, channel=None, guild=None, mid=1234):
        self.content = content
        self.author = author or FakeUser(42)
        self.channel = channel or FakeChannel()
        self.guild = guild
        self.id = mid
        self.mentions = []
        self.jump_url = "https://discord.test/x"
        self.reactions = []
        self.replies = []

    async def add_reaction(self, emoji):
        self.reactions.append(emoji)

    async def remove_reaction(self, emoji, who):
        if emoji in self.reactions:
            self.reactions.remove(emoji)

    async def reply(self, content, **kw):
        self.replies.append(content)


# ── 載入 router（給最小環境，不連 Discord）────────────────────────
@pytest.fixture(scope="module")
def R(tmp_path_factory):
    env = ROOT / "router" / ".env"
    created = False
    if not env.exists():
        env.write_text("OWNER_USER_ID=42\nGUILD_ID=99\nDISCORD_TOKEN_ROUTER=x\n", encoding="utf-8")
        created = True
    # 狀態庫一定要換掉：測試會寫入 chains（跳數），寫進正式的 router_state.db
    # 等於「跑一次測試就讓真實頻道被算了好幾跳」。
    os.environ.update({"OWNER_USER_ID": "42", "GUILD_ID": "99", "DISCORD_TOKEN_ROUTER": "x",
                       "CH_AGENT_HEALTH": "1", "CH_FORGE": "2", "CH_ALERTS": "3",
                       "TD_STATE_DB": str(tmp_path_factory.mktemp("state") / "router_state.db")})
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("td_router", ROOT / "router" / "discord_router.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    yield mod
    if created:
        env.unlink(missing_ok=True)


def _prepare(R, aid, monkeypatch, llm_text="這是回覆", outbox_files=()):
    """把外部依賴換掉：不呼叫 claude、不碰 guard、不查額度、**不看真的 outbox**。

    agent_dir 一定要換掉。否則測試會讀 `agents/<aid>/outbox/` 的真實內容——
    Blacksheep 的機器上那裡有上一次跑剩的檔案，於是 NO_REPLY 測試在他那邊掛、
    在乾淨的 checkout 上過。測試不該依賴工作目錄的殘留狀態。
    """
    tmp = Path(tempfile.mkdtemp(prefix=f"td-{aid}-"))
    (tmp / "outbox").mkdir()
    for name in outbox_files:
        (tmp / "outbox" / name).write_text("x", encoding="utf-8")
    monkeypatch.setattr(R, "agent_dir", lambda a, _t=tmp: _t)
    ch = FakeChannel()
    R.bots[aid] = type("B", (), {"user": FakeUser(9000 + hash(aid) % 100, bot=True, name=aid)})()
    R.queues.setdefault(aid, asyncio.Queue())

    async def fake_claude(a, prompt, tid, model_override=None):
        return llm_text, {"model": "sonnet", "ms": 1, "input_tokens": 1, "output_tokens": 1}

    async def fake_script(a, cmd, extra):
        return "程式輸出"

    async def fake_thread(msg, aid_, cron):
        return ch

    async def fake_hist(c):
        return ""

    monkeypatch.setattr(R, "run_claude", fake_claude)
    monkeypatch.setattr(R, "run_script", fake_script)
    monkeypatch.setattr(R, "ensure_thread", fake_thread)
    monkeypatch.setattr(R, "thread_history", fake_hist)
    monkeypatch.setattr(R, "guard_check", lambda a: None)
    monkeypatch.setattr(R, "calls_last_hour", lambda a: 0)
    return ch


def test_handle_llm_agent_runs_end_to_end(R, monkeypatch):
    """LLM 型 Agent：整條路徑跑完，訊息送出，表情從 👀 走到 ✅。"""
    ch = _prepare(R, "ceo", monkeypatch)
    msg = FakeMessage("<@9000> !status", guild=FakeGuild(99))
    asyncio.run(R.handle("ceo", msg))
    assert ch.sent, f"沒有送出任何訊息；表情：{msg.reactions}"
    assert "✅" in msg.reactions, f"最後應該是 ✅，實際：{msg.reactions}"
    assert "❌" not in msg.reactions


def test_handle_does_not_set_attributes_on_the_message(R, monkeypatch):
    """__slots__ 的 Message 不能被掛屬性——這正是 v3.0.11 的那個 bug。"""
    _prepare(R, "ceo", monkeypatch)
    msg = FakeMessage("<@9000> hi", guild=FakeGuild(99))
    asyncio.run(R.handle("ceo", msg))          # 掛屬性就會在這裡 AttributeError
    for name in ("_agent", "_aid", "agent"):
        assert not hasattr(msg, name), f"handle() 往 Message 掛了 {name}"


def test_handle_no_reply_path(R, monkeypatch):
    """NO_REPLY 是合法輸出：不貼訊息，表情走到 💤。"""
    ch = _prepare(R, "chart", monkeypatch, llm_text="NO_REPLY")
    msg = FakeMessage("<@9000> 有事嗎", guild=FakeGuild(99))
    asyncio.run(R.handle("chart", msg))
    assert msg.reactions[-1] == "💤", msg.reactions
    assert not ch.sent, "NO_REPLY 不該貼任何訊息"


def test_handle_reports_failure_instead_of_dying(R, monkeypatch):
    """LLM 失敗時：表情變 ❌，並且不把例外往外丟（worker 才不會被連累）。"""
    ch = _prepare(R, "chart", monkeypatch)

    async def boom(*a, **k):
        raise RuntimeError("claude exit 1：故意的")

    monkeypatch.setattr(R, "run_claude", boom)
    monkeypatch.setattr(R.bots["chart"], "get_channel", lambda cid: ch, raising=False)
    msg = FakeMessage("<@9000> 分析", guild=FakeGuild(99))
    asyncio.run(R.handle("chart", msg))
    assert "❌" in msg.reactions, msg.reactions


def test_react_never_raises_even_without_aid(R):
    """表情失敗絕不能中斷主流程。"""
    msg = FakeMessage("x")
    asyncio.run(R.react(msg, "👀"))
    asyncio.run(R.react(msg, "✅", remove="👀", aid="不存在的agent"))
    assert "✅" in msg.reactions


def test_no_reply_with_leftover_outbox_files_does_not_post_the_words(R, monkeypatch):
    """LLM 說 NO_REPLY、outbox 卻有檔案：檔案要送，但貼出去的不能是「NO_REPLY」四個字。

    這條路徑是 Blacksheep 的機器先撞到的——他的 agents/chart/outbox/ 有上一次跑剩的檔案。
    殘留通常代表上一次寫完檔案就崩潰 / 斷線，所以這裡同時要留一筆 warning。
    """
    ch = _prepare(R, "chart", monkeypatch, llm_text="NO_REPLY", outbox_files=("report.md",))
    msg = FakeMessage("<@9000> 有事嗎", guild=FakeGuild(99))
    asyncio.run(R.handle("chart", msg))
    assert ch.sent, "outbox 有檔案就該送出去"
    assert "NO_REPLY" not in "".join(ch.sent), ch.sent
    assert msg.reactions[-1] == "✅", msg.reactions


# ── v3.0.13：跳數計數器把排程也算成一跳（「已達 28 跳上限」洗版）──────────

def _msg_from_router(R, text="[CRON:x] 檢查"):
    """模擬 TD-ROUTER 發出的排程訊息——作者是 Bot，但這是一件新工作。"""
    return FakeMessage(text, author=FakeUser(7777, bot=True, name="TD-ROUTER"), guild=FakeGuild(99))


def test_cron_messages_do_not_accumulate_hops(R, monkeypatch):
    """同一個頻道連續 10 次排程，每一次都要正常處理。

    v3.0.12 的行為：排程訊息由 TD-ROUTER（Bot）發出 → 被算成「Agent 又傳了一跳」，
    而跳數只有人類發言才會歸零。於是第 7 次排程之後，那個頻道的每一次排程都只回
    「傳遞已達 N 跳上限」，N 還一直往上加。實際看到的是 28。
    """
    _prepare(R, "risk", monkeypatch)
    cid = next(_CID)
    for i in range(10):
        msg = _msg_from_router(R)
        msg.channel.id = cid                         # 同一個頻道
        asyncio.run(R.handle("risk", msg, cron_job="risk-account-check"))
        assert "🛑" not in msg.reactions, f"第 {i+1} 次排程被跳數上限擋下：{msg.reactions}"


def test_agent_to_agent_still_capped(R, monkeypatch):
    """排程不算跳數，但 Agent 互相觸發**仍然**要被擋——保護不能被順手拆掉。"""
    _prepare(R, "risk", monkeypatch)
    last = None
    cid = next(_CID)
    for _ in range(R.CFG.get("max_hops", 6) + 1):
        last = FakeMessage("接著看", author=FakeUser(9001, bot=True, name="TD-CHART"),
                           guild=FakeGuild(99))
        last.channel.id = cid                        # 同一個頻道＝同一條鏈
        asyncio.run(R.handle("risk", last))
    assert "🛑" in last.reactions, last.reactions


def test_chain_escalates_to_the_human_only_once(R, monkeypatch):
    """一條鏈只吵人一次。上限訊息本身不該變成新的洗版來源。"""
    _prepare(R, "risk", monkeypatch)
    replies = []
    cid = next(_CID)
    for _ in range(R.CFG.get("max_hops", 6) + 6):
        m = FakeMessage("接著看", author=FakeUser(9001, bot=True, name="TD-CHART"),
                        guild=FakeGuild(99))
        m.channel.id = cid
        asyncio.run(R.handle("risk", m))
        replies += m.replies
    stops = [r for r in replies if "上限" in r or "來回" in r]
    assert len(stops) == 1, f"上限訊息貼了 {len(stops)} 次：{stops}"
    assert f"<@{R.OWNER_ID}>" in stops[0], stops[0]


def test_hop_limit_notice_does_not_ping_another_agent(R, monkeypatch):
    """跳數上限的訊息 @ 的是人，不是 TD-CEO。

    原本 @ 的是 CEO。但這條鏈已經滿了，CEO 一被 @ 進來也會立刻撞到同一個上限——
    於是中止訊息自己變成洗版來源，而 CEO 看起來像「都不處理」。
    """
    _prepare(R, "risk", monkeypatch)
    tid = str(next(_CID))
    R.STATE.execute("INSERT OR REPLACE INTO chains VALUES(?,?,?,?,?)",
                    (tid, R.CFG.get("max_hops", 6) - 1, 0, time.time(), 0)); R.STATE.commit()
    m = FakeMessage("接著看", author=FakeUser(9001, bot=True, name="TD-CHART"), guild=FakeGuild(99))
    m.channel.id = int(tid)
    asyncio.run(R.handle("risk", m))
    stop = next(r for r in m.replies if "跳上限" in r)
    assert f"<@{R.OWNER_ID}>" in stop, stop
    for aid in R.CFG["agents"]:
        assert R.mention_of(aid) not in stop, f"中止訊息 @ 了 {aid}，它進來只會再撞一次上限"


def test_idle_chain_resets(R):
    """一條鏈閒置夠久就算結束——不然頻道的計數器會跨天累加。"""
    tid = f"idle-{next(_CID)}"
    for _ in range(3):
        R.chain_bump(tid, from_bot=True)
    assert R.chain_state(tid)[0] == 3
    R.STATE.execute("UPDATE chains SET updated=? WHERE thread_id=?",
                    (time.time() - R.CHAIN_IDLE_RESET - 1, tid)); R.STATE.commit()
    assert R.chain_state(tid)[0] == 0
    assert R.chain_bump(tid, from_bot=True)[0] == 1


def test_cap_notice_does_not_mention_the_replied_bot(R, monkeypatch):
    """中止訊息不能因為「回覆」而 @ 到上一個發言的 Agent。

    Discord 的 reply 預設會 @ 被回覆訊息的作者。中止訊息是回覆，所以它自己就
    @ 了上一個 Agent → 對方被觸發 → 也撞上限 → 回覆又 @ 回來。實測跑到 9719 跳。
    """
    _prepare(R, "risk", monkeypatch)
    tid = str(next(_CID))
    R.STATE.execute("INSERT OR REPLACE INTO chains VALUES(?,?,?,?,?)",
                    (tid, R.CFG.get("max_hops", 6) - 1, 0, time.time(), 0)); R.STATE.commit()

    seen = {}

    class ReplySpy(FakeMessage):
        async def reply(self, content, **kw):
            seen.update(kw)
            self.replies.append(content)

    m = ReplySpy("接著看", author=FakeUser(9001, bot=True, name="TD-CHART"), guild=FakeGuild(99))
    m.channel.id = int(tid)
    asyncio.run(R.handle("risk", m))
    am = seen.get("allowed_mentions")
    assert am is not None and am.replied_user is False, f"reply 沒有關掉 replied_user：{seen}"


def test_mention_must_be_written_in_the_content(R):
    """只有內容裡真的寫了 <@id> 才算被叫到——被某個 Bot 回覆不算。"""
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "bot.user in msg.mentions" not in src
    assert 'rf"<@!?{bot.user.id}>"' in src


def test_burst_breaker_mutes_a_runaway_channel(R, monkeypatch):
    """不講道理的最後一道閘：同一頻道短時間內暴衝就靜音。

    迴圈保護是講道理的（跳數、輪數），總會有沒想到的路徑繞過它——
    v3.0.13 就是兩隻 Bot 互相回覆，幾分鐘跑到 9719 跳。這道閘不看原因，只看速率。
    """
    _prepare(R, "risk", monkeypatch)
    tid = str(next(_CID))
    R._burst.clear(); R._muted.clear()
    ok = [R.burst_ok(tid) for _ in range(R.BURST_LIMIT + 5)]
    assert all(ok[:R.BURST_LIMIT]), "正常流量不該被擋"
    assert not any(ok[R.BURST_LIMIT:]), "超過上限之後必須閉嘴"
    assert tid in R._muted


# ── v3.0.22：Router 自動 BUG_REPORT 被算成一跳（「FORGE 已達 51 跳上限」）──────

class _SpyChannel(FakeChannel):
    """記下 send 的內容，並讓送出的訊息看起來是 TD-ROUTER 發的。"""
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.msgs: list[FakeMessage] = []

    async def send(self, content=None, **kw):
        self.sent.append(content or "")
        m = FakeMessage(content or "", author=self.author, channel=self, guild=FakeGuild(99))
        self.msgs.append(m)
        return m


def _router_bot(R, monkeypatch, ch):
    rb = type("RB", (), {"user": FakeUser(7777, bot=True, name="TD-ROUTER"),
                         "get_channel": lambda self, cid: ch})()
    monkeypatch.setitem(R.bots, "router", rb)
    R._bug_sent.clear()
    return rb


def _failing(R, aid, monkeypatch, err="script exit 1：No module named 'yaml'"):
    _prepare(R, aid, monkeypatch)

    async def boom(*a, **k):
        raise RuntimeError(err)
    monkeypatch.setattr(R, "run_claude", boom)
    monkeypatch.setattr(R, "run_script", boom)


def test_router_bug_reports_do_not_accumulate_hops_in_forge(R, monkeypatch):
    """排程每次失敗都 @FORGE。這些報修是新工作，FORGE 必須每一則都收得到。

    v3.0.21 以前：BUG_REPORT 由失敗的 Agent 的 Bot 發出 → 算成一跳 →
    第 6 則之後 FORGE 只回 🛑，實測累加到 51 跳，修復路徑靜默失效。
    """
    forge_ch = _SpyChannel(FakeUser(7777, bot=True, name="TD-ROUTER"))
    forge_ch.id = next(_CID)
    _router_bot(R, monkeypatch, forge_ch)
    _prepare(R, "forge", monkeypatch)
    for i in range(R.CFG.get("max_hops", 6) + 4):
        # 每次不同的錯誤，避免被去重擋掉
        _failing(R, "watch", monkeypatch, err=f"script exit 1：錯誤 {i}")
        asyncio.run(R.handle("watch", _msg_from_router(R), cron_job="watch-heartbeat"))
        report = forge_ch.msgs[-1]
        assert "BUG_REPORT" in report.content
        _prepare(R, "forge", monkeypatch)
        asyncio.run(R.handle("forge", report))
        assert "🛑" not in report.reactions, f"第 {i+1} 則 BUG_REPORT 被跳數上限擋下：{report.reactions}"


def test_same_failure_is_reported_once_within_dedup_window(R, monkeypatch):
    """同一個排程每 15 分鐘失敗一次，不能每次都叫醒 FORGE（燒額度）。"""
    ch = _SpyChannel(FakeUser(7777, bot=True))
    _router_bot(R, monkeypatch, ch)
    for _ in range(4):
        _failing(R, "watch", monkeypatch)
        asyncio.run(R.handle("watch", _msg_from_router(R), cron_job="watch-heartbeat"))
    assert len([s for s in ch.sent if "BUG_REPORT" in s]) == 1, ch.sent


def test_forge_failing_on_router_bug_report_goes_to_the_human(R, monkeypatch):
    """FORGE 處理自動報修時自己失敗，不能再報修給自己（無限自我報修）。"""
    ch = _SpyChannel(FakeUser(7777, bot=True))
    _router_bot(R, monkeypatch, ch)
    _failing(R, "forge", monkeypatch)
    report = FakeMessage("<@9000> ❌ BUG_REPORT 自動產生", author=FakeUser(7777, bot=True),
                         guild=FakeGuild(99))
    asyncio.run(R.handle("forge", report))
    assert ch.sent, "應該通知人"
    assert "BUG_REPORT 自動產生" not in ch.sent[-1], ch.sent
    assert f"<@{R.OWNER_ID}>" in ch.sent[-1]


def test_only_router_messages_count_as_new_work(R, monkeypatch):
    """Agent 的輸出寫成 `[CRON:x]` 或 BUG_REPORT 格式，不能把跳數歸零。"""
    _router_bot(R, monkeypatch, FakeChannel())
    spoof = FakeMessage("[CRON:x] ❌ BUG_REPORT", author=FakeUser(9001, bot=True, name="TD-CHART"))
    assert not R.from_router(spoof)
    assert R.from_router(FakeMessage("x", author=FakeUser(7777, bot=True)))
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "if m and from_router(msg): cron = m.group(1)" in src
