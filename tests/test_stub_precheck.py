"""stub_precheck.py：佔位程式期間讓每 5 分鐘的 RISK/EXEC 排程安靜——但任何疑慮都必須照常執行。

跳過一個真正的帳戶熔斷／棘輪／對帳是會賠錢的錯；多開一個空 thread 只是吵。
所以這裡測的主要是「什麼時候**不能** SKIP」。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("stub_precheck", ROOT / "scripts" / "stub_precheck.py")
SP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SP)

STUB = '''"""
{name} — NOT_IMPLEMENTED stub

佔位。
"""
import sys
IMPLEMENTED = {impl}


def main():
    sys.exit(0)
'''


@pytest.fixture
def env(tmp_path):
    def make(mode="DEMO", name="executor.py", impl="set()", body=None):
        params = tmp_path / "strategy_params.yaml"
        params.write_text(yaml.safe_dump({"mode": mode}), encoding="utf-8")
        target = tmp_path / name
        target.write_text(body if body is not None else STUB.format(name=name, impl=impl), encoding="utf-8")
        return target, params
    return make


def test_stub_in_demo_is_skipped(env):
    target, params = env()
    assert SP.decide(target, "ratchet", params)[0] == "SKIP"


def test_live_mode_always_runs(env):
    target, params = env(mode="LIVE")
    assert SP.decide(target, "ratchet", params)[0] == "RUN"


def test_implemented_subcommand_runs(env):
    target, params = env(impl='{"ratchet"}')
    assert SP.decide(target, "ratchet", params)[0] == "RUN"
    assert SP.decide(target, "reconcile", params)[0] == "SKIP"
    target, params = env(impl='set(["reconcile"])')
    assert SP.decide(target, "reconcile", params)[0] == "RUN"


def test_real_implementation_runs(env):
    """換掉檔頭＝真的實作了。"""
    target, params = env(body='"""executor.py — 下單、棘輪、對帳"""\nimport sys\n')
    assert SP.decide(target, "ratchet", params)[0] == "RUN"


def test_large_file_with_leftover_marker_runs(env):
    """實作了卻忘了改檔頭：行數超過上限就不信任標記。"""
    body = STUB.format(name="executor.py", impl="set()") + "\n".join(f"x{i} = {i}" for i in range(SP.STUB_MAX_LINES))
    target, params = env(body=body)
    assert SP.decide(target, "ratchet", params)[0] == "RUN"


def test_marker_must_name_the_file_on_the_first_line(env):
    target, params = env(body='"""\n說明：這裡曾經是 NOT_IMPLEMENTED stub\n"""\n')
    assert SP.decide(target, "ratchet", params)[0] == "RUN"


def test_anything_unreadable_runs(env, tmp_path):
    target, params = env()
    assert SP.decide(tmp_path / "missing.py", "ratchet", params)[0] == "RUN"
    bad, params = env(body="def (:\n")
    assert SP.decide(bad, "ratchet", params)[0] == "RUN"
    params.write_text(": : :", encoding="utf-8")
    assert SP.decide(target, "ratchet", params)[0] == "RUN"


def test_scheduler_wires_the_three_five_minute_jobs():
    jobs = {j["name"]: j for j in yaml.safe_load((ROOT / "router" / "scheduler.yaml").read_text(encoding="utf-8"))["jobs"]}
    assert "engine/risk_gate.py --account-check" in jobs["risk-account-check"]["precheck"]
    assert "engine/executor.py ratchet" in jobs["exec-ratchet"]["precheck"]
    assert "engine/executor.py reconcile" in jobs["exec-reconcile"]["precheck"]


def test_router_budget_delay_is_configurable():
    src = (ROOT / "router" / "discord_router.py").read_text(encoding="utf-8")
    assert "asyncio.sleep(900)" not in src
    assert 'CFG.get("budget_defer_minutes"' in src
    cfg = yaml.safe_load((ROOT / "router" / "agents.yaml").read_text(encoding="utf-8"))
    assert cfg["budget_defer_minutes"] == 5
