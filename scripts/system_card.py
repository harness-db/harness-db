"""Render one HARNESS-DB system's 38 cells as a Markdown "cell card".

Usage
    python scripts/system_card.py <system_id> [--out docs/launch/cards/]
    python scripts/system_card.py --top 20 --by stars --out docs/launch/cards/

A card is what we attach when we write to a system's maintainers: the system, its pinned version
with a link to the commit, then one table per layer (dimension, value or state, confidence, the
verbatim quote, the locator, the coder's note, and a prefilled "wrong cell" issue link), the
system's silent design cells ordered by how silent the whole field is on them, and a footer with
the explorer permalink.

Inputs (read-only)
    data/systems.json                       the release: 38 cells per system
    schema/dimensions.json                  dimension ids, keys, layers, names
    data/coding_frame.csv                   stars snapshot, stratum, sampling weight, repo URL
    data/analysis/summary_one_screen.csv    field-level (weighted) not_reported rate per dimension

Rules (deterministic: no clock, no network, no randomness)

1. Cell state comes from ``harnessdb.core.cell_state`` and the quote/locator split from
   ``harnessdb.core.split_evidence``, so the card, the loader and the paper agree.
2. A coded cell shows its value, confidence, quote, locator and note. A ``not_reported`` or
   ``unresolved`` cell shows the state and the coder's note, and nothing in the quote or locator
   columns: nothing is written that the release does not hold.
3. Locators become links only when the target is determined by the data:
   ``path[:line[-line]][ (section)]@sha`` links to the file (and line) at that commit in the
   system's GitHub repository; the commit is expanded to the pinned full hash when the locator's
   short hash is its prefix. A bare repository path with no commit (``README.md``) links to the
   file at the pinned commit and is marked with a dagger, because the locator itself names no
   commit. ``arXiv:<id>`` links to the arXiv abstract; a URL links to itself. Anything else
   (``paper Sec. 3.2``, ``repository evidence header``) stays plain text.
4. ``--top N --by stars`` ranks systems that are weight-bearing (sampling weight > 0 in the frame)
   and have a GitHub repository URL, by the frame's stars snapshot (descending; ties by id), and
   keeps one system per repository. Two ids are the same repository when their normalized URLs
   match, or when the repository names and star snapshots are identical (an organization rename,
   e.g. ``all-hands-ai/openhands`` and ``openhands/openhands``). The index lists the siblings.
5. "Silent cells you can settle fastest" lists the system's ``not_reported`` cells on the 31 design
   dimensions (layers A-H), ordered by the field-level weighted ``not_reported`` rate (descending;
   ties by dimension id). The first three are the ones a maintainer is asked about.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harnessdb.core import cell_state, split_evidence

SYSTEMS = ROOT / "data" / "systems.json"
SCHEMA = ROOT / "schema" / "dimensions.json"
FRAME = ROOT / "data" / "coding_frame.csv"
SUMMARY = ROOT / "data" / "analysis" / "summary_one_screen.csv"

REPO_SLUG = "harness-db/harness-db"
ISSUE_BASE = f"https://github.com/{REPO_SLUG}/issues/new"
EXPLORER = "https://harness-db.github.io/harness-db/"
ZENODO_DOI = "10.5281/zenodo.23031354"
DESIGN_LAYERS = tuple("ABCDEFGH")
DAGGER = "†"

_SHA_LOC = re.compile(
    r"^(?P<path>[^\s@():]+?)"
    r"(?::L?(?P<l1>\d+)(?:-L?(?P<l2>\d+))?)?"
    r"(?:\s*\((?P<sec>[^()]*)\))?"
    r"@(?P<sha>[0-9a-f]{7,40})$"
)
_BARE_PATH = re.compile(
    r"^(?P<path>(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]{1,8})"
    r"(?::L?(?P<l1>\d+)(?:-L?(?P<l2>\d+))?)?"
    r"(?:\s*\((?P<sec>[^()]*)\))?$"
)
_ARXIV = re.compile(r"arXiv[:\s]*(?P<id>\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)
_HEX = re.compile(r"(?<![0-9A-Za-z])([0-9a-f]{7,40})(?![0-9A-Za-z])")
_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|])")


# ------------------------------------------------------------------------------ loading


def load_schema(path: Path = SCHEMA) -> tuple[list[dict], dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    layers = {layer["id"]: layer["name"] for layer in raw["layers"]}
    return raw["dimensions"], layers


def load_systems(path: Path = SYSTEMS) -> dict[str, dict]:
    return {s["id"]: s for s in json.loads(path.read_text(encoding="utf-8"))}


def load_frame(path: Path = FRAME) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["system_id"]: r for r in csv.DictReader(fh)}


def load_field_silence(path: Path = SUMMARY) -> dict[str, float]:
    """Field-level (weighted) not_reported rate per dimension key; empty if the file is absent."""
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("level") == "dimension" and r.get("rate_not_reported_weighted"):
                out[r["key"]] = float(r["rate_not_reported_weighted"])
    return out


# ------------------------------------------------------------------------------ small helpers


def md(text: object) -> str:
    """Escape text for a Markdown table cell: special characters, pipes, and line breaks."""
    s = " ".join(str(text).split())
    return _MD_SPECIAL.sub(r"\\\1", s)


def parse_repo(url: str | None) -> tuple[str, str, str] | None:
    """``https://github.com/owner/repo[/sub/dir]`` -> ``(owner, repo, "sub/dir/")``; else None."""
    if not url:
        return None
    m = re.match(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)(/[^\s#?]*)?", url.strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    repo = repo.removesuffix(".git")
    sub = (m.group(3) or "").strip("/")
    for prefix in ("tree/", "blob/"):  # .../tree/<ref>/<dir> is a ref, not a subdirectory we know
        if sub.startswith(prefix):
            sub = ""
    return owner, repo, (sub + "/" if sub else "")


def repo_url(system: dict, frame_row: dict | None) -> str | None:
    url = (system.get("urls") or {}).get("repo") or (frame_row or {}).get("repo_url") or None
    return url.strip() if url else None


def parse_pinned(value: object) -> tuple[str | None, str | None, str | None]:
    """Split a ``pinned_version`` value into (label, sha, date). Any part may be None."""
    if not value or not isinstance(value, str):
        return None, None, None
    s = value.strip()
    date = _DATE.search(s)
    after_at = s.split("@", 1)[1] if "@" in s else s
    sha = None
    for m in _HEX.finditer(after_at):
        tok = m.group(1)
        if re.search(r"[a-f]", tok) or len(tok) >= 12:
            sha = tok
            break
    label = s.split("@", 1)[0].strip() if "@" in s else None
    if label is None and sha:
        label = s[: s.find(sha)].strip() or None
    if label:
        label = re.sub(r"^(tag:|ref:)\s*", "", label).strip() or None
    return label, sha, date.group(1) if date else None


def stars_of(system: dict, frame_row: dict | None) -> int | None:
    raw = (frame_row or {}).get("stars")
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        pass
    v = (system.get("coding", {}).get("stars") or {}).get("value")
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def weight_of(frame_row: dict | None) -> float:
    try:
        return float((frame_row or {}).get("weight") or 0)
    except ValueError:
        return 0.0


def value_text(value: object, sep: str = ", ") -> str:
    if isinstance(value, list):
        return sep.join(str(v) for v in value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def issue_link(system_id: str, dim: dict | None = None, current: str | None = None) -> str:
    params = {"template": "wrong_cell.yml"}
    if dim is None:
        params["title"] = f"[wrong cell] {system_id} / <dimension>"
        params["system"] = system_id
    else:
        params["title"] = f"[wrong cell] {system_id} / {dim['key']}"
        params["system"] = system_id
        params["dimension"] = f"{dim['id']} {dim['key']}"
        if current is not None:
            params["current"] = current
    return ISSUE_BASE + "?" + urlencode(params, quote_via=quote)


def explorer_link(system_id: str) -> str:
    return f"{EXPLORER}#system={quote(system_id, safe='')}"


def _blob(repo: tuple[str, str, str], sha: str, path: str, l1: str | None, l2: str | None) -> str:
    owner, name, sub = repo
    url = f"https://github.com/{owner}/{name}/blob/{sha}/{quote(sub + path)}"
    if l1:
        url += f"#L{l1}" + (f"-L{l2}" if l2 else "")
    return url


def locator_link(locator: str | None, repo: tuple[str, str, str] | None,
                 pinned_sha: str | None) -> str:
    """Render a locator as Markdown: a link when the target is determined, else escaped text."""
    if not locator:
        return ""
    loc = locator.strip()
    shown = md(loc)
    m = _SHA_LOC.match(loc)
    if m and repo and ("." in m.group("path") or "/" in m.group("path")):
        sha = m.group("sha")
        if pinned_sha and pinned_sha.startswith(sha):
            sha = pinned_sha
        return f"[{shown}]({_blob(repo, sha, m.group('path'), m.group('l1'), m.group('l2'))})"
    m = _BARE_PATH.match(loc)
    if m and repo and pinned_sha:
        url = _blob(repo, pinned_sha, m.group("path"), m.group("l1"), m.group("l2"))
        return f"[{shown}]({url}){DAGGER}"
    m = _ARXIV.search(loc)
    if m:
        return f"[{shown}](https://arxiv.org/abs/{m.group('id')})"
    if re.match(r"^https?://\S+$", loc):
        return f"[{shown}]({loc})"
    return shown


def paper_link(pid: str) -> str:
    if pid.startswith("arxiv:"):
        aid = pid.split(":", 1)[1]
        return f"[arXiv:{aid}](https://arxiv.org/abs/{aid})"
    return f"`{pid}`"


# ------------------------------------------------------------------------------ the card


def silent_design_cells(system: dict, dims: list[dict], field_silence: dict[str, float]
                        ) -> list[tuple[dict, float | None]]:
    """The system's not_reported design cells, most field-silent first (ties by dimension id)."""
    out = []
    for d in dims:
        if d["layer"] not in DESIGN_LAYERS:
            continue
        if cell_state(system["coding"].get(d["key"], {})) == "not_reported":
            out.append((d, field_silence.get(d["key"])))
    out.sort(key=lambda t: (-(t[1] if t[1] is not None else -1.0), t[0]["id"]))
    return out


def render_card(system: dict, dims: list[dict], layers: dict[str, str],
                frame_row: dict | None, field_silence: dict[str, float]) -> str:
    sid = system["id"]
    coding = system["coding"]
    url = repo_url(system, frame_row)
    repo = parse_repo(url)
    label, sha, date = parse_pinned((coding.get("pinned_version") or {}).get("value"))
    states = {d["key"]: cell_state(coding.get(d["key"], {})) for d in dims}
    n = {s: sum(1 for v in states.values() if v == s) for s in ("coded", "not_reported", "unresolved")}

    lines: list[str] = [f"# {md(system.get('name') or sid)}: HARNESS-DB cell card", ""]
    lines += ["| | |", "|---|---|", f"| System id | `{sid}` |"]
    if sha:
        full = sha
        text = f"{md(label) + ' @ ' if label else ''}`{sha[:12]}`"
        if repo:
            text = f"[{text}](https://github.com/{repo[0]}/{repo[1]}/commit/{full})"
        lines.append(f"| Pinned version | {text}{' (' + date + ')' if date else ''} |")
    else:
        pv = (coding.get("pinned_version") or {}).get("value")
        lines.append(f"| Pinned version | {md(pv) if pv else '`not_reported`'} |")
    if url:
        lines.append(f"| Repository | <{url}> |")
    papers = [p for p in system.get("papers", []) if p.startswith("arxiv:")]
    if papers:
        lines.append(f"| Papers | {', '.join(paper_link(p) for p in papers)} |")
    stars = stars_of(system, frame_row)
    if stars is not None:
        lines.append(f"| Stars (sampling-frame snapshot) | {stars:,} |")
    if frame_row:
        lines.append(f"| Stratum / sampling weight | {frame_row.get('stratum', '')} / "
                     f"{weight_of(frame_row):g} |")
    lines.append(f"| Cells | {len(dims)}: {n['coded']} coded, {n['not_reported']} `not_reported`, "
                 f"{n['unresolved']} `unresolved` |")
    lines.append(f"| Coded on | {system.get('coded_at', '')} |")
    lines.append(f"| Explorer | <{explorer_link(sid)}> |")
    lines += ["", ("Every cell is in one of three states. A **value** carries the verbatim quote it "
                   "rests on and a locator you can re-open. `not_reported` means the sources the coder "
                   "was given were read and are silent: undocumented, not absent, and it is the most "
                   "useful kind of cell to settle. `unresolved` failed validation at release and claims "
                   f"nothing. A locator marked {DAGGER} names a file but no commit; its link opens that "
                   "file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell "
                   "issue."), ""]

    for layer_id, layer_name in layers.items():
        ldims = [d for d in dims if d["layer"] == layer_id]
        if not ldims:
            continue
        lines += [f"## {layer_id}. {md(layer_name)}", "",
                  "| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |",
                  "|---|---|---|---|---|---|---|---|"]
        for d in ldims:
            cell = coding.get(d["key"], {})
            st = states[d["key"]]
            note = md(cell["note"]) if cell.get("note") else ""
            if st == "coded":
                quote_, loc = split_evidence(cell.get("evidence"))
                val = f"`{value_text(cell.get('value')).replace('`', '')}`"
                conf = md(cell.get("confidence") or "")
                q = f"“{md(quote_)}”" if quote_ else ""
                current = value_text(cell.get("value"), sep="|")
                lk = locator_link(loc, repo, sha)
            else:
                val, conf, q, lk, current = f"`{st}`", "", "", "", st
            fix = f"[fix]({issue_link(sid, d, current)})"
            lines.append(f"| {d['id']} | `{d['key']}` | {val} | {conf} | {q} | {lk} | {note} | {fix} |")
        lines.append("")

    silent = silent_design_cells(system, dims, field_silence)
    lines += ["## Silent cells you can settle fastest", ""]
    if silent:
        lines += [("The design cells below are `not_reported` for this system, ordered by how "
                   "often the whole field is silent on them (field-level weighted rate). If you know "
                   "the answer, a quote and a file:line at the pinned commit settles the cell."), ""]
        for i, (d, rate) in enumerate(silent, 1):
            r = f"{100 * rate:.1f}% of the field silent" if rate is not None else "field rate n/a"
            lines.append(f"{i}. {d['id']} `{d['key']}` ({md(d.get('name', ''))}): {r}. "
                         f"[Settle it]({issue_link(sid, d, 'not_reported')})")
    else:
        lines.append("None: every design cell of this system is valued or unresolved.")
    lines += ["", "---", "",
              (f"Is a cell wrong? Open a *wrong cell* issue: <{issue_link(sid)}> (or use the "
               "row's *fix* link, which also fills in the dimension and the current value)."),
              "",
              f"Explorer permalink: <{explorer_link(sid)}>",
              "",
              (f"HARNESS-DB 1.0.0 (doi:{ZENODO_DOI}), data CC BY 4.0. Rendered by "
               "`scripts/system_card.py` from `data/systems.json`."), ""]
    return "\n".join(lines)


# ------------------------------------------------------------------------------ top-N


def _norm_repo(url: str) -> str:
    return re.sub(r"(\.git)?/*$", "", url.strip().lower())


def top_systems(systems: dict[str, dict], frame: dict[str, dict], n: int, by: str = "stars",
                one_per_repo: bool = True) -> list[tuple[str, list[str]]]:
    """The N highest-starred weight-bearing systems with a GitHub repository.

    Returns ``[(system_id, [sibling ids sharing the repository]), ...]``.
    """
    if by != "stars":
        raise ValueError(f"unsupported ranking: {by}")
    cands = []
    for sid, s in systems.items():
        fr = frame.get(sid)
        url = repo_url(s, fr)
        if weight_of(fr) <= 0 or not parse_repo(url):
            continue
        st = stars_of(s, fr)
        if st is None:
            continue
        cands.append((-st, sid, url, st))
    cands.sort()
    picked: list[tuple[str, list[str]]] = []
    keys: dict[tuple, int] = {}
    for _, sid, url, st in cands:
        owner_repo = parse_repo(url)
        k1 = ("url", _norm_repo(url))
        k2 = ("name+stars", owner_repo[1].lower(), st)
        hit = keys.get(k1, keys.get(k2)) if one_per_repo else None
        if hit is not None:
            picked[hit][1].append(sid)
            continue
        if len(picked) >= n:
            continue
        keys[k1] = keys[k2] = len(picked)
        picked.append((sid, []))
    return picked


def render_index(rows: list[tuple[str, list[str]]], systems: dict[str, dict],
                 frame: dict[str, dict], dims: list[dict]) -> str:
    lines = ["# Cell cards: the 20 highest-starred coded systems" if len(rows) == 20
             else f"# Cell cards: the {len(rows)} highest-starred coded systems", "",
             ("Weight-bearing systems with a GitHub repository, ranked by the sampling frame's "
              "stars snapshot, one per repository. Regenerate with `python scripts/system_card.py "
              f"--top {len(rows)} --by stars --out docs/launch/cards/`."),
             "", "| # | System | Repository | Stars | Pinned | Coded | `not_reported` | Also in the release |",
             "|---:|---|---|---:|---|---:|---:|---|"]
    for i, (sid, sibs) in enumerate(rows, 1):
        s, fr = systems[sid], frame.get(sid)
        url = repo_url(s, fr)
        owner, name, _ = parse_repo(url)
        label, sha, _ = parse_pinned((s["coding"].get("pinned_version") or {}).get("value"))
        st = [cell_state(s["coding"].get(d["key"], {})) for d in dims]
        pinned = f"{md(label) if label else ''} `{sha[:12]}`" if sha else "n/a"
        also = ", ".join(f"`{x}`" for x in sibs)
        lines.append(f"| {i} | [{md(s.get('name') or sid)}]({sid}.md) | [{owner}/{name}]({url}) | "
                     f"{stars_of(s, fr):,} | {pinned.strip()} | {st.count('coded')} | "
                     f"{st.count('not_reported')} | {also} |")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------ CLI


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("system_id", nargs="?", help="a system id from data/systems.json")
    ap.add_argument("--out", type=Path, help="directory to write <id>.md into (default: stdout)")
    ap.add_argument("--top", type=int, help="render the N highest-ranked systems instead")
    ap.add_argument("--by", default="stars", choices=["stars"], help="ranking for --top")
    ap.add_argument("--all-per-repo", action="store_true",
                    help="with --top, do not collapse systems that share a repository")
    args = ap.parse_args(argv)
    if bool(args.system_id) == bool(args.top):
        ap.error("give either a system_id or --top N")

    dims, layers = load_schema()
    systems, frame, silence = load_systems(), load_frame(), load_field_silence()

    if args.system_id:
        if args.system_id not in systems:
            ap.error(f"unknown system id: {args.system_id}")
        card = render_card(systems[args.system_id], dims, layers, frame.get(args.system_id), silence)
        if args.out:
            _write(args.out / f"{args.system_id}.md", card)
            print(args.out / f"{args.system_id}.md")
        else:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stdout.write(card)
        return 0

    rows = top_systems(systems, frame, args.top, args.by, one_per_repo=not args.all_per_repo)
    out = args.out or Path("docs/launch/cards")
    for sid, _ in rows:
        _write(out / f"{sid}.md", render_card(systems[sid], dims, layers, frame.get(sid), silence))
    _write(out / "README.md", render_index(rows, systems, frame, dims))
    for i, (sid, sibs) in enumerate(rows, 1):
        print(f"{i:>2} {sid}" + (f"  (+ {', '.join(sibs)})" if sibs else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
