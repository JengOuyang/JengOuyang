#!/usr/bin/env python3
"""doctor.py — 開工前的環境健檢，以及「claude -p 沒反應」的診斷。

為什麼需要它：
    整套系統的地基是一件事——`claude -p` 能在這台電腦上非互動地跑完並吐出 JSON。
    這件事一旦不成立，Router 會沉默地卡住而不是報錯（它在等 stdout）。
    與其事後猜，不如開工前先驗一次。

用法（在專案根目錄）：
    python scripts/doctor.py              # 全部檢查，含 claude -p 冒煙測試
    python scripts/doctor.py --no-claude  # 跳過會消耗額度的那一項
    python scripts/doctor.py --agent chart  # 順便用某個 Agent 的設定實跑一次

回傳 0 = 可以開工；1 = 有致命問題；2 = 可以開工但有警告。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
from td_proc import child_env   # 子程序也要用 UTF-8 輸出，否則讀取執行緒會炸

ROOT = Path(__file__).resolve().parents[1]
OK, WARN, BAD = "✅", "⚠️ ", "❌"
problems: list[str] = []
warnings: list[str] = []


def say(mark: str, label: str, detail: str = "") -> None:
    print(f"  {mark} {label}" + (f"　{detail}" if detail else ""))


def run(cmd: list[str], timeout: int = 20, stdin: str | None = None):
    """跑一個指令，回傳 (returncode, stdout, stderr)；逾時回 (None, '', 'timeout')。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           input=stdin, cwd=ROOT, env=child_env(),
                           encoding="utf-8", errors="replace")
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except FileNotFoundError:
        return -1, "", "not found"


# ── 1 基本工具 ────────────────────────────────────────────────────
def check_tools() -> None:
    print("\n【1】基本工具")
    v = sys.version_info
    if (v.major, v.minor) < (3, 11):
        problems.append(f"Python {v.major}.{v.minor} 太舊，需要 3.11+")
        say(BAD, f"Python {v.major}.{v.minor}.{v.micro}", "需要 3.11 以上")
    else:
        say(OK, f"Python {v.major}.{v.minor}.{v.micro}")

    for name, args, need in (("git", ["--version"], True),
                             ("node", ["--version"], False),
                             ("sqlite3", ["--version"], False)):
        exe = shutil.which(name)
        if not exe:
            (problems if need else warnings).append(f"找不到 {name}")
            say(BAD if need else WARN, name, "PATH 裡找不到"
                + ("（必要）" if need else "（非必要，但備份與查資料會用到）"))
            continue
        rc, out, _ = run([exe, *args], 10)
        say(OK, name, out.splitlines()[0] if out else "")

    for mod in ("yaml", "discord", "jsonschema", "pytest"):
        try:
            __import__(mod)
            say(OK, f"python -m {mod}")
        except ImportError:
            problems.append(f"缺少 Python 套件：{mod}")
            say(BAD, f"python -m {mod}", "未安裝 → pip install -r requirements.txt")


# ── 1B 專案路徑與虛擬環境 ─────────────────────────────────────────
def check_path_and_venv() -> None:
    """Windows 上最常見的兩個坑：路徑有空格 / 被雲端同步，以及 venv 被搬過家。"""
    print("\n【1B】專案路徑與虛擬環境")
    s = str(ROOT)

    if " " in s:
        warnings.append("專案路徑含空格")
        say(WARN, "路徑含空格", s)
        print("       pip.exe、claude.cmd 這類啟動器在含空格的路徑下容易出引號問題。")
        print("       建議搬到 C:\\trade-desk 之類沒有空格的位置。")
    else:
        say(OK, "路徑無空格")

    low = s.lower().replace("\\", "/")
    synced = [n for n in ("onedrive", "/desktop/", "/documents/", "dropbox", "google drive", "icloud")
              if n in low]
    if synced:
        warnings.append(f"專案位於可能被雲端同步的資料夾（{synced[0]}）")
        say(WARN, "雲端同步資料夾", f"路徑含 {synced[0]}")
        print("       45 個排程每天讀寫 + SQLite 資料庫，同步程式會鎖檔與製造衝突副本。")
        print("       資料庫損毀是真的會發生——建議搬到 C:\\trade-desk。")
    else:
        say(OK, "不在雲端同步資料夾")

    if not s.isascii():
        warnings.append("專案路徑含非 ASCII 字元")
        say(WARN, "路徑含中文或其他非 ASCII 字元", "部分工具編碼處理仍不完整")

    # venv：pip.exe 裡寫死了建立當下的 python 路徑，搬家就會壞
    venv = ROOT / ".venv"
    if not venv.exists():
        say(WARN, ".venv", "尚未建立（步驟 3 會建）")
        return
    broken = False
    cfg = venv / "pyvenv.cfg"
    if cfg.exists():
        home = next((l.split("=", 1)[1].strip()
                     for l in cfg.read_text(encoding="utf-8", errors="replace").splitlines()
                     if l.lower().startswith("home")), "")
        if home and not Path(home).exists():
            broken = True
            problems.append("venv 指向的 python 已不存在（Python 被升級、移除，或 venv 被搬家）")
            say(BAD, ".venv", f"它記錄的 python 在 {home}，那裡已經沒有東西了")
            print("       → 刪掉重建：deactivate；Remove-Item -Recurse -Force .venv；"
                  "python -m venv .venv；python -m pip install -r requirements.txt")

    # 啟動器裡寫死的路徑必須指回這個 venv
    for exe in ("pip.exe", "pip3.exe"):
        f = venv / "Scripts" / exe
        if not f.exists():
            continue
        blob = f.read_bytes()
        hard = [seg for seg in blob.split(b"\x00") if b":\\" in seg and b"python.exe" in seg.lower()]
        for seg in hard:
            try:
                path = seg.decode("utf-8", "ignore").strip()
            except Exception:
                continue
            if "python.exe" in path.lower() and str(venv).lower() not in path.lower():
                problems.append(f"{exe} 裡寫死的 python 路徑不是這個 venv（venv 被搬家或改名）")
                say(BAD, f".venv/Scripts/{exe}", "裡面寫死的路徑指向別的位置")
                print(f"       它指向：{path[:100]}")
                print("       這就是 `Fatal error in launcher: Unable to create process` 的原因。")
                print("       → 刪掉重建：deactivate；Remove-Item -Recurse -Force .venv；"
                      "python -m venv .venv；python -m pip install -r requirements.txt")
                print("       → 或直接用 `python -m pip`，它不看那串寫死的路徑。")
                break
        else:
            say(OK, f".venv/Scripts/{exe}", "路徑一致")
            continue
        break
    else:
        if not broken and ((venv / "Scripts").exists() or (venv / "bin").exists()):
            say(OK, ".venv", "存在且路徑一致")

    # 現在這個 python 是不是就是那個 venv
    if venv.exists() and str(venv).lower() not in sys.prefix.lower():
        warnings.append("目前的 python 不是專案的 .venv")
        say(WARN, "目前的 python", f"{sys.prefix}　（不是 .venv）")
        print("       → 先啟用：.\\.venv\\Scripts\\Activate.ps1")


# ── 2 claude CLI ─────────────────────────────────────────────────
def check_claude(skip: bool, agent: str | None) -> None:
    print("\n【2】Claude Code CLI（整套系統的地基）")
    exe = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
    if not exe:
        problems.append("PATH 裡找不到 claude")
        say(BAD, "claude", "找不到。安裝後**關掉 PowerShell 重開**讓 PATH 生效")
        print("       npm i -g @anthropic-ai/claude-code   或   irm https://claude.ai/install.ps1 | iex")
        return
    say(OK, "claude 位置", exe)

    rc, out, err = run([exe, "--version"], 30)
    if rc is None:
        problems.append("claude --version 逾時——CLI 本身就卡住了")
        say(BAD, "claude --version", "30 秒無回應")
        return
    if rc != 0:
        problems.append(f"claude --version 失敗：{err[:120]}")
        say(BAD, "claude --version", err[:120])
        return
    say(OK, "claude --version", out.splitlines()[0])

    if skip:
        say(WARN, "冒煙測試", "已用 --no-claude 跳過")
        return

    # 這一段就是「claude -p 沒反應」的真正診斷
    print("\n  冒煙測試：非互動模式 + JSON 輸出（會消耗一點額度，最多等 180 秒）")
    cwd = ROOT / "agents" / agent if agent else ROOT
    cmd = [exe, "-p", "--output-format", "json", "--model", "sonnet", "--max-turns", "1"]
    print(f"       {' '.join(cmd)}　（提示詞走 stdin，cwd={cwd.name}）")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input="回覆 OK，不要做任何工具呼叫。", capture_output=True,
                           text=True, timeout=180, cwd=cwd, env=child_env(),
                           encoding="utf-8", errors="replace")
        rc, out, err = r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        rc, out, err = None, "", "timeout"
    dt = time.time() - t0

    if rc is None:
        problems.append("claude -p 180 秒沒有輸出")
        say(BAD, "claude -p", "逾時。最常見的三個原因：")
        print("       (a) 還沒登入 → 先跑 `claude` 進互動模式完成 /login，再回來")
        print("       (b) 它在等 stdin：`claude -p` 不帶提示詞時會讀 stdin，若你也沒給就會永遠等下去")
        print("       (c) 公司網路 / VPN 擋住 api.anthropic.com")
        return
    if rc != 0:
        problems.append(f"claude -p 退出碼 {rc}")
        say(BAD, "claude -p", f"退出碼 {rc}")
        print("       stderr：" + (err[:300] or "（空）"))
        if "login" in (err + out).lower() or "auth" in (err + out).lower():
            print("       → 看起來是未登入：跑 `claude` 進互動模式完成 /login")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        problems.append("claude -p 的輸出不是 JSON")
        say(BAD, "claude -p", "輸出不是合法 JSON——Router 會解析失敗")
        print("       前 200 字：" + out[:200])
        return

    text = data.get("result") or data.get("text") or ""
    say(OK, "claude -p", f"{dt:.1f} 秒、{len(out)} bytes JSON、回覆「{str(text)[:30]}」")
    if "session_id" not in data:
        warnings.append("claude -p 的 JSON 沒有 session_id，Router 的 --resume 會失效")
        say(WARN, "session_id", "不在輸出裡——多輪對話會退化成每次開新 session")


# ── 3 專案自身 ────────────────────────────────────────────────────
def check_project() -> None:
    print("\n【3】專案完整性")
    for script, label in (("build_context.py", "上下文切片"),
                          ("lint_agents.py", "Agent 定義自洽"),
                          ("verify_isolation.py", "職責與權限隔離"),
                          ("verify_docs_claims.py", "文件宣稱與實際一致"),
                          ("sync_sandbox.py", "沙箱設定同步")):
        args = ["--verify"] if script in ("build_context.py", "sync_sandbox.py") else []
        rc, out, err = run([sys.executable, str(ROOT / "scripts" / script), *args], 120)
        if rc == 0:
            say(OK, label)
        else:
            problems.append(f"{script} 失敗")
            say(BAD, label, f"{script} 回傳 {rc}")
            print("       " + "\n       ".join((out or err).splitlines()[-4:]))

    env = ROOT / "router" / ".env"
    BOOT = ["OWNER_USER_ID", "GUILD_ID", "DISCORD_TOKEN_ROUTER"]
    if not env.exists():
        warnings.append("router/.env 還沒建立")
        say(WARN, "router/.env", "尚未建立 → copy router\\.env.example router\\.env（步驟 7）")
    else:
        vals = {}
        for l in env.read_text(encoding="utf-8").splitlines():
            if "=" in l and not l.strip().startswith("#"):
                k, _, v = l.partition("=")
                vals[k.strip()] = v.strip().strip('"').strip("'")
        miss_boot = [k for k in BOOT if not vals.get(k)]
        if miss_boot:
            problems.append(f"router/.env 缺少啟動必填值：{', '.join(miss_boot)}")
            say(BAD, "router/.env", f"缺少啟動必填值：{', '.join(miss_boot)}")
        else:
            tokens = [k for k in vals if k.startswith("DISCORD_TOKEN_") and vals[k]]
            say(OK, "router/.env", f"啟動必填值齊全；已填 {len(tokens)}/16 把 Discord token")
            if len(tokens) < 16:
                warnings.append(f"還有 {16 - len(tokens)} 隻 Bot 沒建（Day 0 階段正常）")
                say(WARN, "Discord Bot", f"{16 - len(tokens)} 隻還沒建——Router 會跳過它們並列出是誰")

    db = ROOT / "data" / "tradedesk.db"
    say(OK if db.exists() else WARN, "資料庫",
        f"{db.stat().st_size/1048576:.1f} MB" if db.exists()
        else "尚未建立（Day 0 步驟 8 會建）")


# ── 4 隔離層級 ────────────────────────────────────────────────────
def check_isolation() -> None:
    print("\n【4】隔離層級（Router 啟動時也會印一次）")
    win = platform.system() == "Windows"
    require = os.environ.get("TD_REQUIRE_SANDBOX", "0") == "1"
    say(OK, "平台", platform.system() + (" (原生，無 OS 層沙箱)" if win else ""))
    if require and win:
        problems.append("TD_REQUIRE_SANDBOX=1 但這是原生 Windows：每次 Agent 呼叫都會失敗")
        say(BAD, "TD_REQUIRE_SANDBOX", "設成 1 但 Windows 沒有沙箱 → 改回 0，或搬進 WSL2")
    elif require:
        bw = shutil.which("bwrap") or shutil.which("bubblewrap")
        if bw:
            say(OK, "L0 OS 層沙箱", f"要求啟用，bubblewrap 在 {bw}")
        else:
            problems.append("TD_REQUIRE_SANDBOX=1 但找不到 bubblewrap")
            say(BAD, "L0 OS 層沙箱", "要求啟用但沒裝 → sudo apt-get install bubblewrap socat")
    else:
        say(WARN, "L0 OS 層沙箱", "未啟用（TD_REQUIRE_SANDBOX=0）")
        print("       目前隔離 = L1 工具層 + L2 worktree + L3 偵測還原。")
        print("       FORGE / LAB 的逃逸路徑抓得到並自動還原，但擋不住。")
        print("       這是 Windows 上的預期狀態，見 docs/12_DIGITAL_BOUNDARY.md。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-claude", action="store_true", help="跳過會消耗額度的冒煙測試")
    ap.add_argument("--agent", help="用某個 Agent 的目錄與設定實跑冒煙測試（例如 chart）")
    a = ap.parse_args()

    print("TRADE-DESK doctor　—　開工前健檢")
    print(f"專案：{ROOT}")

    check_tools()
    check_path_and_venv()
    check_claude(a.no_claude, a.agent)
    check_project()
    check_isolation()

    print("\n" + "─" * 60)
    for w in warnings:
        print(f"  {WARN} {w}")
    for p in problems:
        print(f"  {BAD} {p}")
    if problems:
        print(f"\n{BAD} {len(problems)} 個致命問題——先修完再啟動 Router")
        return 1
    if warnings:
        print(f"\n{OK} 可以開工（{len(warnings)} 個警告，多半是還沒做到的 Day 0 步驟）")
        return 2
    print(f"\n{OK} 全部通過，可以啟動 Router")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
