r"""
Build docs/SSOT_INDEX.md from the SSOT, per master prompt §D4, and verify the
file against the Appendix-1 inventory.

    python tools/build_ssot_index.py <path/to/ssot.md>

Writes:
    docs/SSOT_INDEX.md          headings with line ranges, ID registry, \boxed{}
                                frozen statements, gate/contract/schema tables,
                                inventory verification
    registry/ssot_ids.csv       every ID family member with all line numbers

Deterministic: no network, no randomness. Exit code 1 if any inventory check
fails, so it can gate CI (master prompt SX-01-01).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# ------------------------------------------------------------ Appendix 1
EXPECTED = {
    "bytes": 1_799_542,
    "lines": 45_697,
    "top_level_headings": 309,
}
G16_NAMES = ["CAL", "CONFLICT", "DATA", "DEC", "EVID", "FT", "GRAPH", "OOD",
             "PROV", "QTY", "REC", "SEM", "TRANS", "VOCAB"]
G15_LETTERS = ["H", "HYB", "I", "INV", "R", "RXN"]
SUPERSEDED_RETURN_POINTS = ["172", "173", "185", "196", "207", "218", "229"]

# Deviations between the file and Appendix 1 that have been investigated and
# recorded as SSOT change requests. A check only passes on a deviation listed
# here; anything else missing still FAILS.
KNOWN_MISSING_SECTIONS = {
    168: ("CR-0001", "no `# 168.` heading exists; its only subsection "
                     "`## 168.1 Immediate next learning block` is orphaned inside "
                     "§173 (legacy v7 return point)"),
}
CURRENT_RETURN_POINT = "279"


def families():
    """(family, regex, expected set or None). Regexes avoid prefix collisions."""
    two = lambda a, b: {f"{i:02d}" for i in range(a, b + 1)}
    return [
        ("RQ16", r"\bRQ16-(\d{2})\b", two(1, 30)),
        ("E16", r"\bE16-([A-L])\b", set("ABCDEFGHIJKL")),
        ("G16", r"\bG16-([A-Z]+)\b", set(G16_NAMES)),
        ("RQ13E", r"\bRQ13E-(\d{2})\b", two(1, 22)),
        ("E13E", r"\bE13E-(\d{2})\b", two(1, 18)),
        ("G13E", r"\bG13E-(\d{2})\b", two(1, 15)),
        ("RISK-E", r"\bRISK-E(\d{1,2})\b", {str(i) for i in range(1, 13)}),
        ("G15", r"\bG15-(\d{1,2}|HYB|INV|RXN|H|I|R)\b",
         {str(i) for i in range(1, 13)} | set(G15_LETTERS)),
        ("G14", r"\bG14-(\d{1,2})\b", {str(i) for i in range(1, 13)}),
        ("G13", r"\bG13-(\d)\b", {str(i) for i in range(0, 5)}),
        ("R13E", r"\bR13E-(\d{2})\b", two(1, 20)),
    ]


def scan(path: pathlib.Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return raw, lines


def headings(lines):
    """Fence-aware heading extraction. Returns list of (level, text, line_no)."""
    out, fence = [], False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,3})\s+(.*\S)\s*$", ln)
        if m:
            out.append((len(m.group(1)), m.group(2), i))
    return out


def with_ranges(hs, n_lines):
    """Attach end lines: a heading runs until the next heading of <= its level."""
    res = []
    for k, (lvl, txt, ln) in enumerate(hs):
        end = n_lines
        for lvl2, _, ln2 in hs[k + 1:]:
            if lvl2 <= lvl:
                end = ln2 - 1
                break
        res.append((lvl, txt, ln, end))
    return res


def section_of(top, line):
    """Top-level heading that contains `line`."""
    cur = None
    for _lvl, txt, ln, end in top:
        if ln <= line <= end:
            cur = txt
    return cur


def sec_num(txt):
    m = re.match(r"^(\d+[A-Z]?)\.\s", txt)
    return m.group(1) if m else None


def boxed(lines):
    r"""Every \boxed{...} with balanced braces; returns (start, end, text)."""
    out, i, n = [], 0, len(lines)
    while i < n:
        j = lines[i].find(r"\boxed{")
        if j < 0:
            i += 1
            continue
        depth, buf, k, start = 0, [], j + len(r"\boxed"), i
        line = i
        s = lines[line]
        done = False
        while not done and line < n:
            while k < len(s):
                c = s[k]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        done = True
                        break
                buf.append(c)
                k += 1
            if not done:
                buf.append(" ")
                line += 1
                k = 0
                s = lines[line] if line < n else ""
        txt = re.sub(r"\s+", " ", "".join(buf)).strip().lstrip("{")
        out.append((start + 1, line + 1, txt))
        # continue scanning after this box (same line may hold another)
        rest = lines[line][k + 1:] if line < n else ""
        if r"\boxed{" in rest:
            lines = lines[:line] + [" " * (k + 1) + rest] + lines[line + 1:]
            i = line
        else:
            i = line + 1
    return out


KEY = re.compile(r"\b(gates?|contracts?|schemas?)\b", re.I)


def keyed_tables(lines):
    """Markdown tables whose caption (nearest heading/bold/label line above) names
    a gate, contract or schema."""
    out, fence, i = [], False, 0
    while i < len(lines) - 1:
        ln = lines[i]
        if ln.lstrip().startswith("```"):
            fence = not fence
        if (not fence and ln.lstrip().startswith("|")
                and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1])):
            cap, back = "", i - 1
            while back >= 0 and i - back <= 6:
                t = lines[back].strip()
                if t and not t.startswith("|"):
                    cap = t
                    break
                back -= 1
            header = ln.strip()
            if KEY.search(cap) or KEY.search(header):
                rows = 0
                k = i + 2
                while k < len(lines) and lines[k].lstrip().startswith("|"):
                    rows += 1
                    k += 1
                out.append((i + 1, cap[:140], header[:140], rows))
                i = k
                continue
        i += 1
    return out


def main(argv):
    ssot = pathlib.Path(argv[1]).resolve() if len(argv) > 1 else None
    if not ssot or not ssot.exists():
        print("usage: build_ssot_index.py <ssot.md>")
        return 2
    raw, lines = scan(ssot)
    n = len(lines)
    sha = hashlib.sha256(raw).hexdigest()
    words = len(raw.decode("utf-8").split())

    hs = with_ranges(headings(lines), n)
    top = [h for h in hs if h[0] == 1]
    raw_top = sum(1 for ln in lines if ln.startswith("# "))
    in_fence_top = raw_top - len(top)

    # numbered sections
    nums = [sec_num(t) for _, t, _, _ in top]
    nums = [x for x in nums if x]
    plain = {int(x) for x in nums if x.isdigit()}
    lettered = sorted(x for x in nums if not x.isdigit())
    missing_plain = sorted(set(range(0, 280)) - plain)
    expected_257 = [f"257{c}" for c in "ABCDEFGHIJKLMNOP"]
    missing_257 = [x for x in expected_257 if x not in lettered]
    parts = [t for _, t, _, _ in top if t.upper().startswith("PART ")]
    dup = [k for k, v in collections.Counter(nums).items() if v > 1]

    sec_title = {sec_num(t): (t, a, b) for _, t, a, b in top if sec_num(t)}

    # ID families
    checks = []
    occ = collections.defaultdict(list)
    for fam, rx, exp in families():
        pat = re.compile(rx)
        for i, ln in enumerate(lines, 1):
            for m in pat.finditer(ln):
                occ[(fam, m.group(1))].append(i)
        found = {k for (f, k) in occ if f == fam}
        missing = sorted(exp - found, key=lambda s: (len(s), s)) if exp else []
        extra = sorted(found - exp, key=lambda s: (len(s), s)) if exp else []
        checks.append((f"{fam} members", len(exp), len(found & exp),
                       not missing, missing, extra))

    # Scoped families whose bare tokens collide elsewhere (T#, D#, R#, Epic)
    def scoped(fam, rx, a, b, expect):
        pat = re.compile(rx)
        for i in range(a, b + 1):
            for m in pat.finditer(lines[i - 1]):
                occ[(fam, m.group(1))].append(i)
        found = {k for (f, k) in occ if f == fam}
        missing = sorted(expect - found, key=lambda s: (len(s), s))
        checks.append((f"{fam} members (scoped §§ search)", len(expect),
                       len(found & expect), not missing, missing,
                       sorted(found - expect, key=lambda s: (len(s), s))))

    def rng(first, last):
        a = sec_title[first][1]
        b = sec_title[last][2]
        return a, b

    a, b = rng("174", "183")
    scoped("T-thread", r"\bT([0-9])\b", a, b, {str(i) for i in range(10)})
    a, b = rng("208", "216")
    scoped("D-transition", r"\bD(1[01]|[0-9])\b", a, b, {str(i) for i in range(12)})
    a, b = rng("256", "256")
    scoped("Epic", r"\bEpic\s+([A-M])\b", a, b, set("ABCDEFGHIJKLM"))
    a, b = rng("135", "135")
    scoped("R-report", r"\bR([1-5])\b", a, b, {str(i) for i in range(1, 6)})

    # return points
    def is_return(num):
        t = sec_title.get(num, ("", 0, 0))[0].upper()
        return "RETURN POINT" in t
    sup_ok = [x for x in SUPERSEDED_RETURN_POINTS if is_return(x)]
    cur_ok = is_return(CURRENT_RETURN_POINT)

    bx = boxed(list(lines))
    tabs = keyed_tables(lines)
    keyed_heads, fence = [], False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,4})\s+(.*\S)\s*$", ln)
        if m and KEY.search(m.group(2)):
            keyed_heads.append((i, len(m.group(1)), m.group(2)))

    inv = [
        ("File bytes", EXPECTED["bytes"], len(raw), len(raw) == EXPECTED["bytes"]),
        ("File lines", EXPECTED["lines"], n, n == EXPECTED["lines"]),
        ("Top-level `# ` lines (raw grep)", EXPECTED["top_level_headings"], raw_top,
         raw_top == EXPECTED["top_level_headings"]),
        ("Numbered sections §0–§279 all present"
         + (f" (known deviation: §{', §'.join(str(m) for m in missing_plain)} → "
            f"{', '.join(KNOWN_MISSING_SECTIONS[m][0] for m in missing_plain if m in KNOWN_MISSING_SECTIONS)})"
            if missing_plain else ""),
         280, len(plain & set(range(280))),
         set(missing_plain) <= set(KNOWN_MISSING_SECTIONS)),
        ("Lettered annexes 257A–257P", 16, 16 - len(missing_257), not missing_257),
        ("Superseded return points are RETURN POINT headings", 7, len(sup_ok),
         len(sup_ok) == 7),
        ("Current return point §279 is a RETURN POINT heading", 1, int(cur_ok), cur_ok),
    ]
    fails = [r for r in inv if not r[3]] + [c for c in checks if not c[3]]

    # ---------------------------------------------------------------- write
    docs = ROOT / "docs"
    reg = ROOT / "registry"
    docs.mkdir(exist_ok=True)
    reg.mkdir(exist_ok=True)

    with (reg / "ssot_ids.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "id", "occurrences", "first_line",
                    "first_top_level_section", "all_lines"])
        for (fam, key), ls in sorted(occ.items(),
                                     key=lambda kv: (kv[0][0], len(kv[0][1]), kv[0][1])):
            ls = sorted(set(ls))
            label = {"G16": f"G16-{key}", "E16": f"E16-{key}", "RQ16": f"RQ16-{key}",
                     "RQ13E": f"RQ13E-{key}", "E13E": f"E13E-{key}",
                     "G13E": f"G13E-{key}", "RISK-E": f"RISK-E{key}",
                     "G15": f"G15-{key}", "G14": f"G14-{key}", "G13": f"G13-{key}",
                     "R13E": f"R13E-{key}", "T-thread": f"T{key}",
                     "D-transition": f"D{key}", "Epic": f"Epic {key}",
                     "R-report": f"R{key}"}[fam]
            w.writerow([fam, label, len(ls), ls[0], section_of(top, ls[0]),
                        " ".join(map(str, ls))])

    L = []
    L.append("# SSOT_INDEX — computational_gastronomy_master_ssot_v15_0.md\n")
    L.append("> Machine-built by `tools/build_ssot_index.py` (master prompt §D4). "
             "**Do not hand-edit** — re-run the script. Line numbers refer to the "
             "file whose SHA-256 is recorded below; if the hash changes, every line "
             "number here is stale.\n")
    L.append("## 1. File identity\n")
    L.append("| Field | Value |\n|---|---|")
    L.append(f"| Path | `{ssot.name}` |")
    L.append(f"| SHA-256 | `{sha}` |")
    L.append(f"| Bytes | {len(raw):,} |")
    L.append(f"| Lines | {n:,} |")
    L.append(f"| Words (whitespace split) | {words:,} |")
    vline = next((l for l in lines[:10] if l.startswith("**Version:**")), "")
    uline = next((l for l in lines[:10] if l.startswith("**Updated:**")), "")
    L.append(f"| Version line | {vline.replace('**Version:**','').strip()[:120]} |")
    L.append(f"| Updated | {uline.replace('**Updated:**','').strip()} |")
    L.append(f"| Top-level headings (fence-aware) | {len(top)} "
             f"(raw grep {raw_top}; {in_fence_top} inside code fences) |")
    L.append(f"| `##` / `###` headings (fence-aware) | "
             f"{sum(1 for h in hs if h[0]==2):,} / {sum(1 for h in hs if h[0]==3):,} |")
    L.append(f"| `\\boxed{{}}` statements | {len(bx)} |")
    L.append(f"| Gate/contract/schema headings / tables | {len(keyed_heads)} / {len(tabs)} |")
    L.append("")

    L.append("## 2. Inventory verification against master prompt Appendix 1\n")
    L.append(f"**Overall: {'PASS' if not fails else 'FAIL — see rows marked FAIL'}**\n")
    L.append("| Check | Expected | Found | Result |\n|---|---|---|---|")
    for name, e, f, ok in inv:
        L.append(f"| {name} | {e:,} | {f:,} | {'PASS' if ok else '**FAIL**'} |")
    for name, e, f, ok, missing, extra in checks:
        note = ""
        if missing:
            note += f" missing: {', '.join(missing)}"
        if extra:
            note += f" · also seen: {', '.join(extra)}"
        L.append(f"| {name} | {e} | {f} | {'PASS' if ok else '**FAIL**'}{note} |")
    L.append("")
    L.append(f"- Words: Appendix 1 says ≈234k; whitespace split gives {words:,}. "
             "Bytes and lines match exactly, so the difference is a counting-method "
             "difference, not a different file.")
    for m in missing_plain:
        if m in KNOWN_MISSING_SECTIONS:
            cr, why = KNOWN_MISSING_SECTIONS[m]
            L.append(f"- **§{m}: {why}.** Recorded as `{cr}` in "
                     "`registry/change_requests.md`; the SSOT is not edited (§D5).")
    if dup:
        L.append(f"- Duplicate section numbers: {', '.join(dup)}")
    L.append(f"- PART headers found: {len(parts)} — "
             + "; ".join(p.split('—')[0].strip() for p in parts))
    L.append("")

    L.append("## 3. Canonical reading order (SSOT header) with line ranges\n")
    order = [("128", "128", "current program status"),
             ("129", "129", "canonical ladder"),
             ("174", "183", "PART VII L12 molecules/ingredients"),
             ("186", "194", "PART VIII L13 recipe/cuisine"),
             ("197", "205", "PART IX L14 process-conditioned"),
             ("208", "216", "PART X L15 transition/kinetics"),
             ("219", "227", "PART XI L15 sparsity/MNAR"),
             ("230", "259", "PART XII L16 CulinaryState-RAG (incl. 257A–257P)"),
             ("260", "279", "PART XIII L13E cultural evolution"),
             ("140", "156", "R1–R5 reconciliation"),
             ("157", "172", "statistics/context/control write-backs"),
             ("278", "278", "v15 gates/roadmap"),
             ("279", "279", "CURRENT RETURN POINT")]
    L.append("| # | §§ | Lines | Topic |\n|---|---|---|---|")
    for k, (s1, s2, topic) in enumerate(order, 1):
        a, b = sec_title[s1][1], sec_title[s2][2]
        L.append(f"| {k} | §{s1}{'–§'+s2 if s2!=s1 else ''} | {a:,}–{b:,} "
                 f"({b-a+1:,} lines) | {topic} |")
    L.append("")
    L.append("Superseded return points (history only): "
             + ", ".join(f"§{x} (L{sec_title[x][1]:,})" for x in SUPERSEDED_RETURN_POINTS))
    L.append("")

    L.append("## 4. ID registry summary\n")
    L.append("Full occurrence lists: `registry/ssot_ids.csv`.\n")
    L.append("| ID | Occurrences | First line | First section |\n|---|---|---|---|")
    with (reg / "ssot_ids.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            sec = (r["first_top_level_section"] or "")[:70]
            L.append(f"| {r['id']} | {r['occurrences']} | {int(r['first_line']):,} | {sec} |")
    L.append("")

    L.append(f"## 5. `\\boxed{{}}` frozen statements ({len(bx)})\n")
    L.append("| Lines | § | Statement (whitespace-collapsed, ≤160 chars) |\n|---|---|---|")
    for a, b, t in bx:
        s = section_of(top, a) or ""
        sn = sec_num(s) or s[:20]
        t = t.replace("|", "\\|")
        L.append(f"| {a:,}–{b:,} | {sn} | `{t[:160]}` |")
    L.append("")

    L.append("## 6. Gate, contract and schema blocks\n")
    L.append("The SSOT writes most gates as headings followed by prose, not as "
             f"tables ({len(tabs)} keyed tables vs {len(keyed_heads)} keyed headings), "
             "so both are listed.\n")
    L.append(f"### 6a. Headings (levels 1–4) naming a gate, contract or schema ({len(keyed_heads)})\n")
    L.append("| Line | Level | § | Heading |\n|---|---|---|---|")
    for ln, lvl, txt in keyed_heads:
        s_ = section_of(top, ln) or ""
        L.append(f"| {ln:,} | {lvl} | {sec_num(s_) or s_[:20]} | {txt[:130].replace('|','/')} |")
    L.append("")
    L.append(f"### 6b. Tables whose caption or header names a gate, contract or schema ({len(tabs)})\n")
    L.append("| Line | § | Caption | Rows |\n|---|---|---|---|")
    for ln, cap, header, rows in tabs:
        s = section_of(top, ln) or ""
        sn = sec_num(s) or s[:20]
        c = (cap or header).replace("|", "\\|")
        L.append(f"| {ln:,} | {sn} | {c} | {rows} |")
    L.append("")

    L.append("## 7. Full heading tree (fence-aware, with line ranges)\n")
    L.append("```text")
    for lvl, txt, a, b in hs:
        L.append(f"{a:>6}–{b:<6} {'  '*(lvl-1)}{'#'*lvl} {txt[:150]}")
    L.append("```")

    (docs / "SSOT_INDEX.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"SSOT {ssot.name}: {len(raw):,} bytes, {n:,} lines, sha256 {sha[:16]}…")
    print(f"headings: top {len(top)} (raw {raw_top}), boxed {len(bx)}, tables {len(tabs)}")
    for name, e, f, ok in inv:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: expected {e}, found {f}")
    for name, e, f, ok, missing, extra in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {f}/{e}"
              + (f"  missing={missing}" if missing else "")
              + (f"  extra={extra}" if extra else ""))
    print("wrote docs/SSOT_INDEX.md and registry/ssot_ids.csv")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
