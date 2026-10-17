#!/usr/bin/env python3
"""MSX機種・部品辞書 MCPサーバー(最小版)

同じフォルダのCSV5本を読み、機種・部品・互換情報を返す。
CSVは呼び出しのたびに読み直すので、データを編集しても再起動は不要。
"""
import csv
import os
import re
import unicodedata
from pathlib import Path

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

DATA_DIR = Path(os.environ.get("MSX_DATA_DIR", Path(__file__).resolve().parent))
mcp = _Server("msx-dictionary")

ALIASES = {
    "ソニー": "sony",
    "パナソニック": "panasonic",
    "松下": "panasonic",
    "カワイ": "kawai",
    "河合": "kawai",
    "ミツミ": "mitsumi",
}

CAUTION = (
    "※確度が「未確認」「報告あり」の項目は断定せず、出典を確かめるよう案内してください。"
    "「互換」は実機での動作確認を意味しません。"
)


# ---------- 下請け ----------
def norm(s: str) -> str:
    """表記ゆれを吸収する(全角半角・大文字小文字・ハイフン・空白・メーカー名の日英)。"""
    s = unicodedata.normalize("NFKC", s or "").lower()
    for k, v in ALIASES.items():
        s = s.replace(k, v)
    return re.sub(r"[\s\-_‐−–ー・/]", "", s)


def load(name: str) -> list[dict]:
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tokens(query: str) -> list[str]:
    return [norm(t) for t in re.split(r"[\s、,，]+", query) if norm(t)]


def haystack(row: dict) -> str:
    return norm(" ".join(v for v in row.values() if v))


def score(row: dict, toks: list[str]) -> int:
    h = haystack(row)
    return sum(1 for t in toks if t in h)


def v(x: str) -> str:
    return x if x else "—"


def source_line(row: dict) -> str:
    parts = []
    if row.get("source_url"):
        parts.append(row["source_url"])
    if row.get("source_note"):
        parts.append(row["source_note"])
    kind = f"[{row['source_type']}] " if row.get("source_type") else ""
    return kind + (" / ".join(parts) if parts else "出典なし")


def find_machines(q: str) -> list[dict]:
    nq = norm(q)
    rows = load("msx_machines.csv")
    exact = [r for r in rows if nq in (norm(r["id"]), norm(r["model"]))]
    if exact:
        return exact
    return [r for r in rows if nq and (nq in norm(r["id"]) or nq in norm(r["model"]))]


def find_parts(q: str) -> list[dict]:
    nq = norm(q)
    parts = load("msx_parts.csv")
    numbers = load("msx_part_numbers.csv")
    hit_ids = []
    for p in parts:
        if nq in (norm(p["id"]), norm(p["name"])):
            hit_ids.append(p["id"])
    for n in numbers:
        if nq and nq == norm(n["part_number"]):
            hit_ids.append(n["part_id"])
    if not hit_ids:
        for p in parts:
            if nq and (nq in norm(p["id"]) or nq in norm(p["name"])):
                hit_ids.append(p["id"])
        for n in numbers:
            if nq and nq in norm(n["part_number"]):
                hit_ids.append(n["part_id"])
    seen, out = set(), []
    by_id = {p["id"]: p for p in parts}
    for i in hit_ids:
        if i not in seen and i in by_id:
            seen.add(i)
            out.append(by_id[i])
    return out


def part_numbers_of(pid: str) -> str:
    rows = [n for n in load("msx_part_numbers.csv") if n["part_id"] == pid]
    if not rows:
        return "—"
    return "、".join(f"{n['maker']} {n['part_number']}" for n in rows)


# ---------- ツール ----------
@mcp.tool()
def search_machines(query: str, limit: int = 10) -> str:
    """MSXの機種をキーワードで探す。

    メーカー名・型番・世代(MSX2+など)・年・メモの語に一致する機種を、一致数の多い順に返す。
    短いキーワードをスペース区切りで渡す(例: "Sony MSX2" / "ソニー 1987" / "turboR")。
    """
    toks = tokens(query)
    if not toks:
        return "キーワードを入れてください。"
    scored = [(score(r, toks), r) for r in load("msx_machines.csv")]
    hits = sorted((x for x in scored if x[0] > 0), key=lambda x: -x[0])[:limit]
    if not hits:
        return f"「{query}」に一致する機種は辞書にありません。(辞書の収録は一部の機種のみです)"
    lines = [f"「{query}」に一致する機種: {len(hits)}件", ""]
    for s, r in hits:
        lines.append(f"- {r['maker']} {r['model']}(id: {r['id']}) / {v(r['generation'])} / {v(r['year'])}")
    lines += ["", "詳細は get_machine に id か型番を渡してください。"]
    return "\n".join(lines)


@mcp.tool()
def get_machine(machine: str) -> str:
    """機種1台の詳細(電源・映像出力・搭載部品・出典)を返す。machine は id か型番(例: "HB-F1XD")。"""
    found = find_machines(machine)
    if not found:
        return f"「{machine}」に一致する機種は辞書にありません。search_machines で探してください。"
    if len(found) > 1:
        names = "、".join(f"{r['model']}(id: {r['id']})" for r in found)
        return f"候補が複数あります: {names}。id で指定してください。"
    r = found[0]
    out = [
        f"# {r['maker']} {r['model']}(id: {r['id']})",
        f"- 世代: {v(r['generation'])} / 発売: {v(r['year'])} / 地域: {v(r['region'])}",
        f"- 前身: {v(r['predecessor'])}",
        f"- 電源: {v(r['power'])}",
        f"- 映像出力: {v(r['video_out'])}",
        f"- メモ: {v(r['notes'])}",
        f"- 出典: {source_line(r)}",
    ]
    parts = {p["id"]: p for p in load("msx_parts.csv")}
    eqs = load("msx_part_equivalents.csv")
    links = [l for l in load("msx_links.csv") if l["machine_id"] == r["id"]]
    if links:
        out += ["", "## 関連する部品"]
        for l in links:
            p = parts.get(l["part_id"])
            if not p:
                continue
            line = (
                f"- {p['name']}(id: {p['id']}、番号: {part_numbers_of(p['id'])}) "
                f"[{l['relation']} / 確度: {l['confidence']}] {l['note']}"
            )
            for e in eqs:
                if p["id"] in (e["part_a"], e["part_b"]):
                    other = e["part_b"] if e["part_a"] == p["id"] else e["part_a"]
                    o = parts.get(other, {"name": other})
                    line += f"\n    ※互換とされる部品: {o['name']} [{e['relation']} / 確度: {e['confidence']}](詳細は find_compatible)"
            out.append(line)
    out += ["", CAUTION]
    return "\n".join(out)


@mcp.tool()
def search_parts(query: str, limit: int = 10) -> str:
    """部品・周辺機器をキーワードで探す(カテゴリ、名前、故障の特徴、メーカー別の部品番号が対象)。

    例: "アダプター" / "ベルト" / "EMC-NX0039" / "1-464-877-11"
    """
    toks = tokens(query)
    if not toks:
        return "キーワードを入れてください。"
    numbers = load("msx_part_numbers.csv")
    scored = []
    for p in load("msx_parts.csv"):
        extra = " ".join(n["part_number"] + " " + n["maker"] for n in numbers if n["part_id"] == p["id"])
        row = dict(p)
        row["_numbers"] = extra
        scored.append((score(row, toks), p))
    hits = sorted((x for x in scored if x[0] > 0), key=lambda x: -x[0])[:limit]
    if not hits:
        return f"「{query}」に一致する部品は辞書にありません。"
    lines = [f"「{query}」に一致する部品: {len(hits)}件", ""]
    for s, p in hits:
        lines.append(f"- {p['name']}(id: {p['id']}、{p['category']}、番号: {part_numbers_of(p['id'])})")
    lines += ["", "互換・使われている機種は find_compatible に id か番号を渡してください。"]
    return "\n".join(lines)


@mcp.tool()
def find_compatible(part: str) -> str:
    """部品の互換情報を返す。part は id・名前・部品番号のどれでもよい(例: "AC-HB3" / "DAMCNX0039XT")。

    メーカー別の部品番号、互換とされる別の部品、その部品を使う機種(確度つき)を返す。
    """
    found = find_parts(part)
    if not found:
        return f"「{part}」に一致する部品は辞書にありません。search_parts で探してください。"
    if len(found) > 1:
        if _same_group([x["id"] for x in found]):
            return "\n\n---\n\n".join(_compat_report(x) for x in found)
        names = "、".join(f"{p['name']}(id: {p['id']})" for p in found)
        return f"候補が複数あります: {names}。id で指定してください。"
    return _compat_report(found[0])


def _same_group(ids: list[str]) -> bool:
    """検索に複数ヒットした部品が、互換の表で互いにつながっているか。"""
    eqs = load("msx_part_equivalents.csv")
    seen, todo = {ids[0]}, [ids[0]]
    while todo:
        cur = todo.pop()
        for e in eqs:
            for a, b in ((e["part_a"], e["part_b"]), (e["part_b"], e["part_a"])):
                if a == cur and b not in seen:
                    seen.add(b)
                    todo.append(b)
    return all(i in seen for i in ids)


def _compat_report(p: dict) -> str:
    parts = {x["id"]: x for x in load("msx_parts.csv")}
    machines = {m["id"]: m for m in load("msx_machines.csv")}
    links = load("msx_links.csv")

    out = [
        f"# {p['name']}(id: {p['id']})",
        f"- カテゴリ: {p['category']}",
        f"- 部品番号: {part_numbers_of(p['id'])}",
        f"- 仕様: {v(p['spec'])}",
        f"- よくある故障: {v(p['typical_failure'])}",
        f"- 出典: {source_line(p)}",
    ]

    eq_rows = [e for e in load("msx_part_equivalents.csv") if p["id"] in (e["part_a"], e["part_b"])]
    eq_ids = []
    if eq_rows:
        out += ["", "## 互換とされる部品"]
        for e in eq_rows:
            other = e["part_b"] if e["part_a"] == p["id"] else e["part_a"]
            eq_ids.append(other)
            o = parts.get(other, {"name": other})
            out.append(
                f"- {o['name']}(id: {other}、番号: {part_numbers_of(other)}) "
                f"[{e['relation']} / 確度: {e['confidence']}] {e['note']} 出典: {source_line(e)}"
            )

    def machine_lines(pid: str, label: str) -> list[str]:
        ls = []
        for l in links:
            if l["part_id"] == pid and l["machine_id"] in machines:
                m = machines[l["machine_id"]]
                ls.append(f"- {m['maker']} {m['model']} [{l['relation']} / 確度: {l['confidence']}] {l['note']}{label}")
        return ls

    used = machine_lines(p["id"], "")
    if used:
        out += ["", "## この部品に関係する機種"] + used
    for eid in eq_ids:
        more = machine_lines(eid, f"(互換部品 {parts.get(eid, {}).get('name', eid)} 経由)")
        if more:
            out += ["", f"## 互換部品 {parts.get(eid, {}).get('name', eid)} に関係する機種"] + more

    out += ["", CAUTION]
    return "\n".join(out)


# ---------- 症状から探す ----------
CONF_RANK = {"出典記載あり": 0, "報告あり": 1, "未確認": 2}
URGENT_WORDS = ["焦げ", "煙", "発煙", "発火", "火花", "スパーク", "異臭", "臭い", "匂い", "におい",
                "熱い", "発熱", "感電", "燃え", "smoke", "burn", "smell", "spark", "fire"]
URGENT = (
    "【安全のための注意】煙・焦げた匂い・異常な発熱・火花などがある場合は、直ちに電源プラグを抜き(アダプター式はアダプターを外し)、"
    "使用を中止してください。再び通電せず、専門の修理店に相談してください。"
    "(一般的な安全上の注意で、この辞書の出典に基づくものではありません)"
)
SAFETY = (
    "※診断ではなく、出典に書かれた手がかりの一覧です。内蔵電源の機種は内部にAC100Vがあります。"
    "通電したままの作業は避け、不安な場合は専門の修理店に相談してください。基板の改造は自己責任です。"
)


def _linked_part_ids(machine_id: str) -> set[str]:
    """機種に紐づく部品と、それと互換とされる部品のid。"""
    base = {l["part_id"] for l in load("msx_links.csv") if l["machine_id"] == machine_id}
    ids = set(base)
    for e in load("msx_part_equivalents.csv"):
        if e["part_a"] in base:
            ids.add(e["part_b"])
        if e["part_b"] in base:
            ids.add(e["part_a"])
    return ids


@mcp.tool()
def diagnose(symptom: str, machine: str = "", limit: int = 5) -> str:
    """故障の症状から、辞書にある出典付きの手がかり(疑わしい部品・最初に確かめること)を返す。

    symptom にはユーザーの言葉をそのまま渡す(例: "映像が出ない" / "ディスクが読めない" / "黒画面" / "音が歪む")。
    機種が分かっていれば machine に id か型番を渡すと、その機種の情報を優先して返す。
    出力は診断ではなく、出典に書かれた手がかりです。確度が「未確認」のものは断定せず伝えてください。
    """
    nq = norm(symptom)
    if not nq:
        return "症状を入れてください。"
    machines = {m["id"]: m for m in load("msx_machines.csv")}
    mid, mlabel = "", ""
    if machine:
        found = find_machines(machine)
        if not found:
            return f"「{machine}」に一致する機種は辞書にありません。機種を指定せずに症状だけで探すこともできます。"
        if len(found) > 1:
            names = "、".join(f"{r['model']}(id: {r['id']})" for r in found)
            return f"機種の候補が複数あります: {names}。id で指定してください。"
        mid = found[0]["id"]
        mlabel = f"{found[0]['maker']} {found[0]['model']}"

    scored = []
    for r in load("msx_symptoms.csv"):
        hits = [k for k in r["keywords"].split("|") if k and norm(k) in nq]
        if hits:
            scored.append((sum(len(norm(k)) for k in hits), r))
    urgent = any(norm(w) in nq for w in URGENT_WORDS)
    if not scored:
        msg = f"「{symptom}」に当てはまる症状は辞書にありません。list_symptoms で収録している症状を確認できます。"
        return (URGENT + "\n\n" + msg) if urgent else msg

    note = ""
    if mid:
        scoped = [(sc, r) for sc, r in scored if r["machine_id"] in ("", mid)]
        if scoped:
            scored = scoped
        else:
            note = f"※{mlabel}に絞ると候補がないため、他の機種の情報を参考として載せています。"

    best = max(sc for sc, _ in scored)
    if best >= 6:  # 強く一致した候補があれば、弱い一致は省く
        scored = [(sc, r) for sc, r in scored if sc * 2 >= best]

    def key(x):
        sc, r = x
        return (0 if mid and r["machine_id"] == mid else 1, CONF_RANK.get(r["confidence"], 3), -sc)

    scored.sort(key=key)
    shown = scored[:limit]
    parts = {p["id"]: p for p in load("msx_parts.csv")}
    linked = _linked_part_ids(mid) if mid else set()

    head = f"「{symptom}」に当てはまる手がかり: {len(shown)}件" + (f"(機種: {mlabel})" if mid else "")
    out = ([URGENT, ""] if urgent else []) + [head]
    if note:
        out.append(note)
    out.append("")
    for i, (sc, r) in enumerate(shown, 1):
        out.append(f"## 候補{i}: {r['symptom']} [確度: {r['confidence']}]")
        if r["machine_id"]:
            m = machines.get(r["machine_id"])
            if m:
                out.append(f"- 対象機種: {m['maker']} {m['model']}の情報です")
        pids = [x for x in r["part_ids"].split(";") if x]
        if pids:
            for pid in pids:
                p = parts.get(pid)
                if not p:
                    continue
                mark = ""
                if mid and pid not in linked:
                    mark = "(この機種との対応は辞書に未登録。参考)"
                out.append(f"- 疑わしい部品: {p['name']}(id: {pid}、番号: {part_numbers_of(pid)}){mark}")
        else:
            out.append("- 疑わしい部品: 出典では特定されていません")
        out.append(f"- まず確かめること: {r['check_first']}")
        out.append(f"- 出典が述べていること: {r['note']}")
        out.append(f"- 出典: {source_line(r)}")
        out.append("")
    if len(scored) > limit:
        out.append(f"(ほかに{len(scored) - limit}件。limit を増やすと表示します)")
        out.append("")
    out += ["部品の互換や、使われている機種は find_compatible に部品の id か番号を渡してください。", SAFETY, CAUTION]
    return "\n".join(out)


@mcp.tool()
def list_symptoms() -> str:
    """辞書に収録している症状の一覧を返す(どんな症状から探せるかの確認用)。"""
    rows = load("msx_symptoms.csv")
    machines = {m["id"]: m for m in load("msx_machines.csv")}
    out = [f"辞書にある症状: {len(rows)}件", ""]
    for r in rows:
        scope = ""
        if r["machine_id"] and r["machine_id"] in machines:
            m = machines[r["machine_id"]]
            scope = f"(対象: {m['maker']} {m['model']})"
        out.append(f"- {r['symptom']}{scope} [確度: {r['confidence']}]")
    out += ["", "症状の言葉を diagnose に渡すと、疑わしい部品と最初に確かめることを返します。"]
    return "\n".join(out)

if __name__ == "__main__":
    mcp.run()
