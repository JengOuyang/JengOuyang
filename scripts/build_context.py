#!/usr/bin/env python3
"""
build_context.py — 從 shared/（單一真相）生成每個 Agent 的 .context/ 角色切片。

用法：
  python scripts/build_context.py            # 生成所有 Agent 的切片
  python scripts/build_context.py --agent chart
  python scripts/build_context.py --verify   # 只驗證現有切片是否與 shared/ 一致（exit 1 = 不一致）

為什麼要這樣做：
  - 單一真相：規則只寫在 shared/ 一份，永不複製貼上，不會漂移。
  - 認知隔離：每個 Agent 的 context 只有它該知道的條款，避免推理不屬於自己的事。
  - 可驗證：每個切片檔頭帶來源 SHA-256；Agent 開工前驗證，不符就停工。
  - 省 token：CHART 不需要載入帳戶熔斷與棘輪規則。
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
MAP = yaml.safe_load((ROOT / "shared" / "context_map.yaml").read_text(encoding="utf-8"))
CONSTITUTION = ROOT / "shared" / "CONSTITUTION.md"
MISSION = ROOT / "shared" / "MISSION.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_h2(text: str) -> list[tuple[str, str]]:
    """把 Markdown 依 H2 切成 [(標題, 內容含標題)]；H2 之前的前言歸為 ('', 前言)。"""
    parts, cur_title, buf = [], "", []
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            parts.append((cur_title, "".join(buf)))
            cur_title, buf = line.rstrip("\n"), [line]
        else:
            buf.append(line)
    parts.append((cur_title, "".join(buf)))
    return parts


def extract(text: str, wanted: list[str]) -> str:
    """取出標題以 wanted 任一字串開頭的 H2 區段；前言一律保留（含文件說明與版本）。"""
    out = []
    for title, body in split_h2(text):
        if title == "":
            out.append(body)
        elif any(title.startswith(w) for w in wanted):
            out.append(body)
    return "".join(out)


def build_one(agent: str, spec: dict, write: bool) -> dict:
    ctx = ROOT / "agents" / agent / ".context"
    if write:
        ctx.mkdir(parents=True, exist_ok=True)
    manifest = {
        "agent": agent,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "scripts/build_context.py",
        "sources": {},
        "files": [],
        "outputs": {},        # 切片自身的 SHA-256：驗證產物有沒有被改過（不只驗來源）
    }
    # 憲法：逐字複製，全體一致
    const_txt = CONSTITUTION.read_text(encoding="utf-8")
    manifest["sources"]["shared/CONSTITUTION.md"] = sha(CONSTITUTION)
    # 共同認知卡：與憲法同等級，全體逐字一致（目標／框架／知識來源／自問五條）
    manifest["sources"]["shared/MISSION.md"] = sha(MISSION)
    files = {"constitution.md": const_txt, "mission.md": MISSION.read_text(encoding="utf-8")}

    for key, rule in spec.items():
        src_rel = MAP["sources"].get(key)
        if not src_rel:
            continue
        src = ROOT / src_rel
        if not src.exists():
            print(f"  ! 來源不存在，略過：{src_rel}", file=sys.stderr)
            continue
        if rule == "none":
            continue
        text = src.read_text(encoding="utf-8")
        note = ""
        if rule == "full":
            body = text
        elif rule == "core":
            body = extract(text, MAP.get("protocol_core", []))
        elif isinstance(rule, dict):
            secs = rule.get("sections", [])
            body = extract(text, secs) if secs else split_h2(text)[0][1]
            note = rule.get("note", "")
        else:
            body = text
        header = (
            f"<!-- 生成物，請勿手動編輯。來源：{src_rel}@sha256:{sha(src)[:16]} "
            f"生成於 {manifest['generated_at']} -->\n"
        )
        scope = f"\n> **本切片的範圍**：{note}\n" if note else ""
        files[f"{key}.md"] = header + scope + "\n" + body
        manifest["sources"][src_rel] = sha(src)

    import hashlib
    for name, content in files.items():
        manifest["files"].append(name)
        manifest["outputs"][name] = content_sha(content)
        if write:
            (ctx / name).write_text(content, encoding="utf-8")
    if write:
        (ctx / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest



def content_sha(text: str) -> str:
    """雜湊時剔除生成時間戳，讓同樣的輸入在不同機器上得到同樣的雜湊（可重現）。"""
    import hashlib, re
    body = re.sub(r"生成於 [^\n>]*", "生成於 -", text)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

def verify_one(agent: str) -> list[str]:
    """回傳問題清單；空清單 = 通過。"""
    ctx = ROOT / "agents" / agent / ".context"
    mf = ctx / "MANIFEST.json"
    if not mf.exists():
        return [f"{agent}: 缺少 .context/MANIFEST.json（尚未執行 build_context.py）"]
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    problems = []
    for rel, expect in manifest["sources"].items():
        p = ROOT / rel
        if not p.exists():
            problems.append(f"{agent}: 來源已不存在 {rel}")
        elif sha(p) != expect:
            problems.append(f"{agent}: {rel} 已變更但切片未重建（請執行 build_context.py）")
    import hashlib
    for f in manifest["files"]:
        fp = ctx / f
        if not fp.exists():
            problems.append(f"{agent}: 切片檔遺失 {f}")
            continue
        want = manifest.get("outputs", {}).get(f)
        if want is None:
            problems.append(f"{agent}: MANIFEST 沒有 {f} 的輸出雜湊（請重跑 build_context.py）")
        elif content_sha(fp.read_text(encoding="utf-8")) != want:
            problems.append(f"{agent}: 切片檔 {f} 被直接竄改（內容與 MANIFEST 的雜湊不符）——這是隔離被繞過的徵兆")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    agents = [args.agent] if args.agent else list(MAP["slices"].keys())
    if args.verify:
        problems = [p for a in agents for p in verify_one(a)]
        if problems:
            print("上下文完整性驗證失敗：")
            for p in problems:
                print("  -", p)
            return 1
        print(f"上下文完整性 OK（{len(agents)} 個 Agent）")
        return 0

    for a in agents:
        spec = MAP["slices"].get(a)
        if spec is None:
            print(f"! context_map.yaml 沒有 {a} 的切片定義", file=sys.stderr)
            continue
        m = build_one(a, spec, write=True)
        print(f"  {a:9s} → {', '.join(m['files'])}")
    print(f"完成：{len(agents)} 個 Agent 的 .context/ 已重建")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
