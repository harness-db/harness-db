"""Harvest agent leaderboards into one Record per distinct system (protocol section 5,
"agent leaderboards for the outcomes table"; unit of analysis: protocol section 4.1).

Leaderboards and the machine-readable sources used (details in README_grey.md):

  swebench        swebench.com embeds every submission as JSON (``<script id="leaderboard-data">``,
                  splits Verified/Lite/Test/Multimodal/Multilingual). Fallback: the
                  SWE-bench/experiments GitHub repo (``evaluation/<split>/<dir>/metadata.yaml`` +
                  ``results/results.json``) through ``gh api`` and raw.githubusercontent.com.
  hal             hal.cs.princeton.edu/<benchmark> server-rendered tables (9 benchmarks).
  osworld         os-world.github.io/static/data/{osworld_verified_results,self_reported_results}.xlsx
  webarena        the Google Sheet embedded on webarena.dev/og (xlsx export keeps hyperlinks).
  terminal_bench  tbench.ai/leaderboard (Next.js flight payload, Terminal-Bench 4.0) +
                  laude-institute/terminal-bench-leaderboard (Terminal-Bench 1.0 run logs).
                  Terminal-Bench 2.0 rows are not obtainable from any static source (see notes).
  gaia            HF datasets-server rows of gaia-benchmark/results_public (validation + test).
  tau_bench       sierra-research/tau-bench README result tables.
  tau2_bench      taubench.com manifest + submission.json files on the public S3 bucket.

Record: id = ``leaderboard:<family>:<system-slug>``, source = "leaderboard",
query_used = leaderboard family, title = system name, abstract = one-line description plus the
models/scores seen, url = entry site or repo, date = earliest submission date,
extra = {"benchmark", "n_entries", "splits", "entries": [{model, score, metric, date, url,
split, ...}]}.

Rows that are a bare model on the leaderboard's own scaffold are recorded as the system
"<benchmark> reference agent" (protocol 4.1); the original row label is kept in
``entries[].raw_name``.

Usage:
    python scripts/harvest/leaderboards.py [--out data/raw/leaderboards.jsonl] [--count-only]
        [--only swebench,hal,...] [--log-level INFO]

A failing leaderboard is logged and skipped; the script never raises on one bad source.
"""

from __future__ import annotations

import io
import json
import logging
import math
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from common import (
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    normalize_title,
    now_iso,
    print_summary,
    setup_logging,
)

GH = r"C:\Program Files\GitHub CLI\gh.exe"
HAL_BASE = "https://hal.cs.princeton.edu"
HAL_BENCHMARKS = (
    "gaia",
    "swebench_verified_mini",
    "taubench_airline",
    "usaco",
    "corebench_hard",
    "scicode",
    "scienceagentbench",
    "assistantbench",
    "online_mind2web",
)
OSWORLD_XLSX = {
    "verified": "https://os-world.github.io/static/data/osworld_verified_results.xlsx",
    "self-reported": "https://os-world.github.io/static/data/self_reported_results.xlsx",
}
WEBARENA_SHEET = "1M801lEpBbKSNwP-vDBkC_pF7LdyGU1f_ufZb_NWNBZQ"
TBENCH_LIVE = "https://www.tbench.ai/leaderboard"
TBENCH_V1_REPO = "laude-institute/terminal-bench-leaderboard"
GAIA_DATASET = "gaia-benchmark/results_public"
TAU_README = "https://raw.githubusercontent.com/sierra-research/tau-bench/main/README.md"
TAU2_S3 = "https://sierra-tau-bench-public.s3.us-west-2.amazonaws.com/submissions"
SWEBENCH_SITE = "https://www.swebench.com/"
SWEBENCH_REPO = "SWE-bench/experiments"
SWEBENCH_SPLIT_SIZE = {"verified": 500, "lite": 300, "test": 2294, "multimodal": 517, "multilingual": 300}

MODEL_RE = re.compile(
    r"^(gpt|o[1-9]\b|chatgpt|claude|gemini|qwen|llama|deepseek|kimi|glm|grok|mistral|doubao|seed|"
    r"ui-?tars|uitars|opencua|computer-use-preview|operator|aguvis|holo|jedi|os-atlas|internvl|"
    r"cogagent|phi|gemma|minimax|step|hunyuan|nemotron|magma|showui|aria|fara|gui-owl|mai|"
    r"codellama|mixtral|blip|vicuna|palm|text-bison|idefics|llava)",
    re.IGNORECASE,
)
DESCRIPTIONS = {
    "SWE-bench": "Submission to the SWE-bench leaderboard (swebench.com; SWE-bench/experiments)",
    "HAL": "Agent scaffold evaluated on the Holistic Agent Leaderboard (hal.cs.princeton.edu)",
    "OSWorld": "Entry on the OSWorld / OSWorld-Verified computer-use leaderboard (os-world.github.io)",
    "WebArena": "Entry on the WebArena leaderboard (webarena.dev)",
    "Terminal-Bench": "Entry on the Terminal-Bench leaderboard (tbench.ai)",
    "GAIA": "Submission to the GAIA leaderboard (HF gaia-benchmark/leaderboard)",
    "tau-bench": "Agent strategy reported in the tau-bench README (sierra-research/tau-bench)",
    "tau2-bench": "Submission to the tau2-bench leaderboard (taubench.com)",
}


@dataclass
class Entry:
    family: str  # leaderboard family, e.g. "SWE-bench"
    split: str  # split / sub-benchmark, e.g. "Verified"
    system: str
    model: str | None
    score: float | None
    metric: str
    date: str | None = None
    url: str | None = None
    org: str | None = None
    raw_name: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "split": self.split,
            "model": self.model,
            "score": self.score,
            "metric": self.metric,
            "date": self.date,
            "url": self.url,
            "org": self.org,
        }
        if self.raw_name and self.raw_name != self.system:
            d["raw_name"] = self.raw_name
        d.update({k: v for k, v in self.extra.items() if v not in (None, "", [], {})})
        return d


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "unnamed"


def clean(text: Any) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split())


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if math.isnan(float(value)) else float(value)
    m = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(m.group(0)) if m else None


_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def iso_date(value: Any) -> str | None:
    """Best-effort ISO date from the many formats leaderboards use."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001
            return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "nat", "-"):
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{1,2})/(\d{4})$", s)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.? (\d{1,2}),? (\d{4})$", s)
    if m and m.group(1).lower() in _MONTHS:
        return f"{m.group(3)}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"^([A-Za-z]{3})[a-z]* (\d{4})$", s)
    if m and m.group(1).lower() in _MONTHS:
        return f"{m.group(2)}-{_MONTHS[m.group(1).lower()]:02d}"
    m = re.match(r"^(\d{4})$", s)
    if m:
        return s
    return None


def gh_api(endpoint: str, log: logging.Logger, retries: int = 3) -> Any:
    """``gh api`` GET with a small retry on rate-limit errors (pre-authenticated CLI)."""
    cmd = [GH, "api", "-X", "GET", endpoint]
    for attempt in range(retries + 1):
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if proc.returncode == 0:
            return json.loads(proc.stdout) if proc.stdout.strip() else None
        err = (proc.stderr or proc.stdout).strip()
        if attempt < retries and ("rate limit" in err.lower() or "502" in err or "503" in err):
            delay = 15 * (attempt + 1)
            log.warning("gh api %s: %s; retry in %ds", endpoint, err[:120], delay)
            time.sleep(delay)
            continue
        raise HttpError(f"gh api {endpoint}: {err[:300]}")
    raise HttpError(f"gh api {endpoint}: retries exhausted")


def decode_flight(page: str) -> str:
    """Concatenate and unescape the Next.js ``self.__next_f.push`` payloads of a page."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', page, re.DOTALL)
    out = []
    for c in chunks:
        try:
            out.append(c.encode("utf-8", "surrogatepass").decode("unicode_escape", errors="replace"))
        except Exception:  # noqa: BLE001
            out.append(c)
    return "".join(out)


def json_objects_containing(text: str, key: str) -> list[dict[str, Any]]:
    """Return every JSON object embedded in ``text`` that has ``key`` as a top-level member."""
    dec = json.JSONDecoder()
    found: list[dict[str, Any]] = []
    spans: list[tuple[int, int]] = []
    for m in re.finditer(re.escape(f'"{key}"'), text):
        pos = m.start()
        if any(a <= pos < b for a, b in spans):
            continue
        start = pos
        for _ in range(200):  # walk back over candidate '{' until one decodes and holds the key
            start = text.rfind("{", 0, start)
            if start < 0:
                break
            try:
                obj, end = dec.raw_decode(text, start)
            except json.JSONDecodeError:
                continue
            if end <= pos:
                continue
            if isinstance(obj, dict) and key in obj:
                found.append(obj)
                spans.append((start, end))
                break
    return found


# --------------------------------------------------------------------------------------
# SWE-bench
# --------------------------------------------------------------------------------------


def harvest_swebench(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    entries: list[Entry] = []
    try:
        resp = client.get(SWEBENCH_SITE)
        if resp.status_code != 200:
            raise HttpError(f"swebench.com HTTP {resp.status_code}")
        m = re.search(r'<script[^>]*id="leaderboard-data"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            raise HttpError("swebench.com: no <script id=leaderboard-data>")
        boards = json.loads(m.group(1))
        for board in boards:
            split = board.get("name", "?")
            for r in board.get("results", []):
                folder = r.get("folder") or ""
                system = clean(r.get("agent")) or clean(r.get("name"))
                models = [t[7:] for t in r.get("tags", []) if isinstance(t, str) and t.startswith("Model: ")]
                url = r.get("site") or (
                    f"https://github.com/{SWEBENCH_REPO}/tree/main/evaluation/{split.lower()}/{folder}" if folder else None
                )
                entries.append(
                    Entry(
                        family="SWE-bench",
                        split=split,
                        system=system,
                        model=clean(r.get("model_display")) or (", ".join(models) if models else None),
                        score=to_float(r.get("resolved")),
                        metric="% resolved",
                        date=iso_date(r.get("date")) or iso_date(folder[:8]),
                        url=url,
                        org=clean(r.get("agent_org")) or None,
                        raw_name=clean(r.get("name")),
                        extra={
                            "folder": folder,
                            "model_ids": models,
                            "checked": r.get("checked"),
                            "os_system": r.get("os_system"),
                            "os_model": r.get("os_model"),
                            "model_org": r.get("model_org"),
                            "instance_cost": r.get("instance_cost"),
                            "reasoning_effort": r.get("reasoning_effort"),
                        },
                    )
                )
        notes["swebench"] = {"source": SWEBENCH_SITE + " (embedded leaderboard-data JSON)", "splits": {b["name"]: len(b.get("results", [])) for b in boards}}
        return entries
    except Exception as exc:  # noqa: BLE001
        log.warning("swebench.com failed (%s); falling back to GitHub metadata.yaml", exc)
        notes["swebench"] = {"source": f"github:{SWEBENCH_REPO} (fallback)", "site_error": str(exc)[:200]}
    return _swebench_from_github(client, log, notes)


def _swebench_from_github(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    try:
        import yaml
    except ImportError:
        yaml = None
    tree = gh_api(f"repos/{SWEBENCH_REPO}/git/trees/main?recursive=1", log)
    paths = [t["path"] for t in tree.get("tree", []) if re.match(r"^evaluation/[^/]+/[^/]+/metadata\.yaml$", t["path"])]
    have_results = {t["path"].rsplit("/", 2)[0] for t in tree.get("tree", []) if t["path"].endswith("/results/results.json")}
    log.info("SWE-bench experiments: %d metadata.yaml files (tree truncated=%s)", len(paths), tree.get("truncated"))
    entries: list[Entry] = []
    per_split: dict[str, int] = defaultdict(int)
    for p in paths:
        _, split, folder, _ = p.split("/")
        raw = client.get(f"https://raw.githubusercontent.com/{SWEBENCH_REPO}/main/{p}")
        if raw.status_code != 200:
            log.warning("%s: HTTP %s", p, raw.status_code)
            continue
        meta: dict[str, Any] = {}
        if yaml is not None:
            try:
                meta = yaml.safe_load(raw.text) or {}
            except Exception as exc:  # noqa: BLE001
                log.warning("%s: bad yaml (%s)", p, exc)
        info = meta.get("info") or {}
        tags = meta.get("tags") or {}
        resolved = to_float(info.get("resolved"))
        base = p.rsplit("/", 1)[0]
        if resolved is None and base in have_results:
            rr = client.get(f"https://raw.githubusercontent.com/{SWEBENCH_REPO}/main/{base}/results/results.json")
            if rr.status_code == 200:
                try:
                    n = len(rr.json().get("resolved", []))
                    total = SWEBENCH_SPLIT_SIZE.get(split)
                    resolved = round(100.0 * n / total, 2) if total else None
                except Exception as exc:  # noqa: BLE001
                    log.warning("%s/results/results.json unreadable: %s", base, exc)
        models = tags.get("model") or []
        if isinstance(models, str):
            models = [models]
        entries.append(
            Entry(
                family="SWE-bench",
                split=split.capitalize(),
                system=clean(tags.get("agent")) or clean(info.get("name")),
                model=clean(tags.get("model_display")) or (", ".join(map(str, models)) if models else None),
                score=resolved,
                metric="% resolved",
                date=iso_date(folder[:8]),
                url=info.get("site") or info.get("report") or f"https://github.com/{SWEBENCH_REPO}/tree/main/{base}",
                org=clean(tags.get("agent_org") or tags.get("org")) or None,
                raw_name=clean(info.get("name")),
                extra={"folder": folder, "model_ids": [str(m) for m in models], "checked": tags.get("checked"), "os_system": tags.get("os_system")},
            )
        )
        per_split[split] += 1
    notes["swebench"]["splits"] = dict(per_split)
    return entries


# --------------------------------------------------------------------------------------
# HAL
# --------------------------------------------------------------------------------------


def harvest_hal(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    from lxml import html as lhtml

    entries: list[Entry] = []
    per_bench: dict[str, int] = {}
    failures: dict[str, str] = {}
    for bench in HAL_BENCHMARKS:
        url = f"{HAL_BASE}/{bench}"
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                raise HttpError(f"HTTP {resp.status_code}")
            doc = lhtml.fromstring(resp.text)
            tables = doc.xpath("//table")
            if not tables:
                raise HttpError("no <table>")
            table = tables[0]
            # header labels: drop tooltip divs, keep the first words
            headers = []
            for th in table.xpath(".//thead//th"):
                for tip in th.xpath(".//div"):
                    tip.getparent().remove(tip)
                headers.append(clean(th.text_content()))
            rows = table.xpath(".//tbody/tr")
            n = 0
            for tr in rows:
                cells = tr.xpath("./td")
                if len(cells) < 4:
                    continue
                row = {headers[i] if i < len(headers) else f"col{i}": cells[i] for i in range(len(cells))}
                scaffold_cell = row.get("Scaffold")
                if scaffold_cell is None:
                    continue
                links = scaffold_cell.xpath(".//a")
                system = clean(links[0].text_content()) if links else clean(scaffold_cell.text_content())
                agent_href = links[0].get("href") if links else None
                model_cell = row.get("Primary Model") or row.get("Models")
                model = None
                if model_cell is not None:
                    model_links = [clean(a.text_content()) for a in model_cell.xpath(".//a")]
                    model = ", ".join(x for x in model_links if x) or clean(model_cell.text_content()) or None
                acc_cell = row.get("Accuracy")
                acc_text = clean(acc_cell.text_content()) if acc_cell is not None else ""
                acc_m = re.search(r"-?\d+(?:\.\d+)?%", acc_text)
                cost_cell = row.get("Cost (USD)")
                cost_text = clean(cost_cell.text_content()) if cost_cell is not None else ""
                cost_m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", cost_text)
                verified_cell = row.get("Verified")
                verified = bool(verified_cell is not None and "✓" in verified_cell.text_content())
                runs_cell = row.get("Runs")
                traces = row.get("Traces")
                trace_links = traces.xpath(".//a/@href") if traces is not None else []
                extra_cols = {}
                for h, c in row.items():
                    if h not in ("Rank", "Scaffold", "Primary Model", "Models", "Accuracy", "Cost (USD)", "Verified", "Runs", "Traces"):
                        extra_cols[h] = clean(c.text_content())
                entries.append(
                    Entry(
                        family="HAL",
                        split=bench,
                        system=system,
                        model=model,
                        score=to_float(acc_m.group(0)) if acc_m else to_float(acc_text),
                        metric="accuracy %",
                        date=None,
                        url=f"{HAL_BASE}{agent_href}" if agent_href and agent_href.startswith("/") else agent_href,
                        raw_name=system,
                        extra={
                            "cost_usd": to_float(cost_m.group(1)) if cost_m else None,
                            "verified": verified,
                            "runs": clean(runs_cell.text_content()) if runs_cell is not None else None,
                            "traces": trace_links[0] if trace_links else None,
                            "pareto_optimal": "Pareto optimal" in clean(scaffold_cell.text_content()),
                            "accuracy_text": acc_text,
                            **({"columns": extra_cols} if extra_cols else {}),
                        },
                    )
                )
                n += 1
            per_bench[bench] = n
            log.info("HAL %s: %d rows", bench, n)
        except Exception as exc:  # noqa: BLE001
            log.warning("HAL %s failed: %s", bench, exc)
            failures[bench] = str(exc)[:200]
    notes["hal"] = {"source": HAL_BASE + "/<benchmark> server-rendered tables", "benchmarks": per_bench, "failures": failures}
    return entries


# --------------------------------------------------------------------------------------
# OSWorld
# --------------------------------------------------------------------------------------


def _osworld_system(name: str, approach: str | None) -> tuple[str, str | None]:
    """Split an OSWorld row label into (system, model)."""
    name = clean(name)
    m = re.match(r"^(.*?)\s+(?:w/|with)\s+(.+)$", name, re.IGNORECASE)
    if m:
        return clean(m.group(1)), clean(m.group(2))
    approach = (approach or "").lower()
    if "framework" in approach or "agent" in approach:
        return name, None
    if "model" in approach or MODEL_RE.match(name):
        return "OSWorld reference agent", name
    return name, None


def harvest_osworld(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    import pandas as pd

    entries: list[Entry] = []
    sheets_seen: dict[str, int] = {}
    failures: dict[str, str] = {}
    for kind, url in OSWORLD_XLSX.items():
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                raise HttpError(f"HTTP {resp.status_code}")
            book = pd.read_excel(io.BytesIO(resp.content), sheet_name=None)
        except Exception as exc:  # noqa: BLE001
            log.warning("OSWorld %s failed: %s", kind, exc)
            failures[kind] = str(exc)[:200]
            continue
        for sheet, df in book.items():
            split = "Verified" if kind == "verified" else f"self-reported/{sheet}"
            n = 0
            for _, row in df.iterrows():
                name = clean(row.get("Model"))
                if not name or name.lower() == "nan":
                    continue
                approach = clean(row.get("Approach type")) if "Approach type" in df.columns else None
                system, model = _osworld_system(name, approach)
                score = to_float(row.get("Success rate")) if "Success rate" in df.columns else to_float(row.get("Score"))
                paper = clean(row.get("PaperLink"))
                extra = {
                    "approach_type": approach,
                    "institution": clean(row.get("Institution")) or None,
                    "details": clean(row.get("Details")) or None,
                    "max_steps": to_float(row.get("Max steps")) if "Max steps" in df.columns else None,
                    "a11y_tree": clean(row.get("Additional a11y tree used")) or None,
                    "success_total": clean(row.get("Success/Total")) or None,
                    "trajectories": clean(row.get("TrajectoryLink")) or None,
                }
                entries.append(
                    Entry(
                        family="OSWorld",
                        split=split,
                        system=system,
                        model=model,
                        score=score,
                        metric="success rate %",
                        date=iso_date(row.get("Date")),
                        url=paper if paper.startswith("http") else None,
                        org=clean(row.get("Institution")) or None,
                        raw_name=name,
                        extra=extra,
                    )
                )
                n += 1
            sheets_seen[split] = n
    notes["osworld"] = {"source": list(OSWORLD_XLSX.values()), "sheets": sheets_seen, "failures": failures}
    return entries


# --------------------------------------------------------------------------------------
# WebArena
# --------------------------------------------------------------------------------------


def _cell_link(cell: Any) -> str | None:
    h = getattr(cell, "hyperlink", None)
    return h.target if h is not None and getattr(h, "target", None) else None


def harvest_webarena(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    import openpyxl

    url = f"https://docs.google.com/spreadsheets/d/{WEBARENA_SHEET}/export?format=xlsx"
    resp = client.get(url)
    if resp.status_code != 200:
        raise HttpError(f"WebArena sheet export HTTP {resp.status_code}")
    wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=False, data_only=True)
    entries: list[Entry] = []
    per_sheet: dict[str, int] = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows())
        # the header is the first row that has a "Success Rate" column
        hdr_i = next((i for i, r in enumerate(rows) if any("success rate" in clean(c.value).lower() for c in r)), None)
        if hdr_i is None:
            per_sheet[ws.title] = 0
            continue
        header = [clean(c.value) for c in rows[hdr_i]]
        idx = {h: i for i, h in enumerate(header) if h}
        score_col = next(h for h in idx if "success rate" in h.lower())
        date_col = next((h for h in idx if h in ("a", "Release Date", "Date")), None)
        work_col = next((h for h in ("Work", "Result Source") if h in idx), None)
        n = 0
        for r in rows[hdr_i + 1 :]:
            cells = {h: r[i] for h, i in idx.items() if i < len(r)}
            val = {h: clean(c.value) for h, c in cells.items()}
            model_label = val.get("Model", "")
            work = val.get(work_col, "") if work_col else ""
            score = to_float(cells[score_col].value) if score_col in cells else None
            if score is None or not (model_label or work):
                continue
            if work and not work.lower().startswith(("http", "self-reported", "reported by")):
                system = work
            else:
                system = model_label
            model: str | None = model_label or None
            m = re.match(r"^(.*?)\s*\+\s*(.+)$", model_label)
            if m and system != model_label:
                model = m.group(2)
            bench = "VisualWebArena" if "visual" in ws.title.lower() else "WebArena"
            if system.lower() in ("webarena", "visualwebarena") or (
                MODEL_RE.match(system) and " + " not in system and not re.search(r"agent|cua", system, re.IGNORECASE)
            ):
                # the benchmark paper's own baselines (Work/Result Source = the benchmark) or a bare model
                system = f"{bench} reference agent"
            link = None
            for col in (work_col, "Result Source", "Model"):
                if col and col in cells:
                    link = _cell_link(cells[col])
                    if link:
                        break
            entries.append(
                Entry(
                    family="WebArena",
                    split=ws.title,
                    system=system,
                    model=model,
                    score=score,
                    metric="success rate %",
                    date=iso_date(cells[date_col].value) if date_col and date_col in cells else None,
                    url=link,
                    raw_name=f"{work} / {model_label}".strip(" /"),
                    extra={
                        "open": val.get("Open?") or None,
                        "model_type": val.get("Model Type") or None,
                        "inputs": val.get("Inputs") or None,
                        "model_size_b": val.get("Model Size (billion)") or None,
                        "result_source": val.get("Result Source") or None,
                        "trajectories": _cell_link(cells["Traj"]) if "Traj" in cells else None,
                        "note": val.get("Note") or None,
                    },
                )
            )
            n += 1
        per_sheet[ws.title] = n
    notes["webarena"] = {"source": f"Google Sheet {WEBARENA_SHEET} (xlsx export, linked from webarena.dev/og)", "sheets": per_sheet}
    return entries


# --------------------------------------------------------------------------------------
# Terminal-Bench
# --------------------------------------------------------------------------------------


def _tbench_entries_from_flight(text: str, split_default: str) -> list[Entry]:
    boards = {b["id"]: b for b in json_objects_containing(text, "metadata_schema") if "id" in b}
    for m in re.finditer(r'\{"id":"([0-9a-f-]{36})","package_id":"[^"]*","package":"[^"]*"[^{}]*?"title":"([^"]+)"', text):
        boards.setdefault(m.group(1), {"id": m.group(1), "title": m.group(2)})
    out: list[Entry] = []
    for row in json_objects_containing(text, "leaderboard_id"):
        md = row.get("metadata") or {}
        metrics = row.get("metrics") or {}
        if not md:
            continue
        board = boards.get(row.get("leaderboard_id"), {})
        agent = (md.get("agent_display") or {}).get("label") or "?"
        model = (md.get("model_display") or {}).get("label")
        out.append(
            Entry(
                family="Terminal-Bench",
                split=board.get("title") or split_default,
                system=agent,
                model=model,
                score=to_float(metrics.get("accuracy")),
                metric="accuracy %",
                date=iso_date(md.get("date")),
                url=(md.get("agent_display") or {}).get("url"),
                org=(md.get("agent_org") or {}).get("label"),
                raw_name=agent,
                extra={
                    "rank": row.get("rank"),
                    "n_trials": metrics.get("n_trials"),
                    "ci95_half_width": metrics.get("accuracy_ci95_half_width"),
                    "total_cost_usd": metrics.get("total_cost_usd"),
                    "reasoning_effort": md.get("reasoning_effort"),
                    "model_org": (md.get("model_org") or {}).get("label"),
                },
            )
        )
    return out


def harvest_terminal_bench(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    entries: list[Entry] = []
    note: dict[str, Any] = {"sources": {}}
    # (a) live leaderboard (Terminal-Bench 4.0 at time of writing)
    try:
        resp = client.get(TBENCH_LIVE)
        if resp.status_code != 200:
            raise HttpError(f"HTTP {resp.status_code}")
        live = _tbench_entries_from_flight(decode_flight(resp.text), "Terminal-Bench (live)")
        entries.extend(live)
        note["sources"][TBENCH_LIVE] = len(live)
    except Exception as exc:  # noqa: BLE001
        log.warning("Terminal-Bench live page failed: %s", exc)
        note["sources"][TBENCH_LIVE] = f"failed: {exc}"[:200]
    # (b) Terminal-Bench 1.0 run logs on GitHub
    try:
        n = 0
        datasets = gh_api(f"repos/{TBENCH_V1_REPO}/contents/results", log)
        for ds in datasets:
            if ds.get("type") != "dir":
                continue
            subs = gh_api(f"repos/{TBENCH_V1_REPO}/contents/{ds['path']}", log)
            for sub in subs:
                if sub.get("type") != "dir":
                    continue
                m = re.match(r"^(\d{8})_(.+?)_(.+)$", sub["name"])
                if not m:
                    continue
                date, agent, model = m.groups()
                runs = gh_api(f"repos/{TBENCH_V1_REPO}/contents/{sub['path']}", log)
                accs: list[float] = []
                for run in runs:
                    if run.get("type") != "dir":
                        continue
                    rr = client.get(f"https://raw.githubusercontent.com/{TBENCH_V1_REPO}/main/{run['path']}/results.json")
                    if rr.status_code != 200:
                        continue
                    try:
                        acc = rr.json().get("accuracy")
                    except Exception:  # noqa: BLE001
                        acc = None
                    if isinstance(acc, (int, float)):
                        accs.append(float(acc))
                score = round(100.0 * sum(accs) / len(accs), 2) if accs else None
                entries.append(
                    Entry(
                        family="Terminal-Bench",
                        split=f"Terminal-Bench 1.0 ({ds['name']})",
                        system=agent,
                        model=model,
                        score=score,
                        metric="accuracy % (mean of runs)",
                        date=iso_date(date),
                        url=f"https://github.com/{TBENCH_V1_REPO}/tree/main/{sub['path']}",
                        raw_name=sub["name"],
                        extra={"n_runs": len(accs), "run_accuracies": accs},
                    )
                )
                n += 1
        note["sources"][f"github:{TBENCH_V1_REPO}"] = n
    except Exception as exc:  # noqa: BLE001
        log.warning("Terminal-Bench 1.0 GitHub logs failed: %s", exc)
        note["sources"][f"github:{TBENCH_V1_REPO}"] = f"failed: {exc}"[:200]
    # (c) Terminal-Bench 2.0: no static source. The live site only serves the current board,
    # Harbor Hub renders rows client-side from an endpoint that answers 404 without a session,
    # and Wayback captures of the old site hold only the client shell (react-query) or the
    # current board. Recorded as a known gap in grey_notes.md rather than fetched.
    note["sources"]["Terminal-Bench 2.0"] = "not available (client-rendered; no capture with rows)"
    notes["terminal_bench"] = note
    return entries


# --------------------------------------------------------------------------------------
# GAIA
# --------------------------------------------------------------------------------------


def harvest_gaia(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    entries: list[Entry] = []
    per_split: dict[str, int] = {}
    # datasets-server throttles bursts (502 then 429): pace at 2 s with long backoff
    hf = HttpClient(min_interval=2.0, max_retries=8, timeout=60, backoff_base=5.0, backoff_cap=180.0, logger=log)
    for split in ("validation", "test"):
        offset = 0
        n = 0
        while True:
            data = hf.get_json(
                "https://datasets-server.huggingface.co/rows",
                params={"dataset": GAIA_DATASET, "config": "2023", "split": split, "offset": offset, "length": 100},
            )
            rows = data.get("rows", [])
            for item in rows:
                r = item.get("row", {})
                name = clean(r.get("model"))
                if not name:
                    continue
                family = clean(r.get("model_family")) or None
                url = clean(r.get("url"))
                entries.append(
                    Entry(
                        family="GAIA",
                        split=split,
                        system=name,
                        model=family,
                        score=round(100.0 * r["score"], 2) if isinstance(r.get("score"), (int, float)) else None,
                        metric="accuracy %",
                        date=iso_date(r.get("date")),
                        url=url if url.startswith("http") else None,
                        org=clean(r.get("organisation")) or None,
                        raw_name=name,
                        extra={
                            "level1": round(100.0 * r["score_level1"], 2) if isinstance(r.get("score_level1"), (int, float)) else None,
                            "level2": round(100.0 * r["score_level2"], 2) if isinstance(r.get("score_level2"), (int, float)) else None,
                            "level3": round(100.0 * r["score_level3"], 2) if isinstance(r.get("score_level3"), (int, float)) else None,
                            "system_prompt": (clean(r.get("system_prompt")) or None) if len(clean(r.get("system_prompt"))) < 300 else clean(r.get("system_prompt"))[:300] + "...",
                        },
                    )
                )
                n += 1
            total = data.get("num_rows_total", 0)
            offset += len(rows)
            if not rows or offset >= total:
                break
        per_split[split] = n
        log.info("GAIA %s: %d rows", split, n)
    notes["gaia"] = {"source": f"datasets-server.huggingface.co/rows dataset={GAIA_DATASET}", "splits": per_split}
    return entries


# --------------------------------------------------------------------------------------
# tau-bench (README tables) and tau2-bench (taubench.com submissions on S3)
# --------------------------------------------------------------------------------------

TAU_STRATEGY_NAMES = {
    "tc": "tau-bench reference agent (tool-calling)",
    "act": "tau-bench reference agent (Act)",
    "react": "tau-bench reference agent (ReAct)",
}


def harvest_tau_bench(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    resp = client.get(TAU_README)
    if resp.status_code != 200:
        raise HttpError(f"tau-bench README HTTP {resp.status_code}")
    entries: list[Entry] = []
    domain = None
    header: list[str] = []
    for line in resp.text.splitlines():
        if line.startswith("### "):
            domain = line[4:].strip()
            header = []
            continue
        if not line.startswith("|") or domain is None:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not header:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        label = cells[0]
        link = re.search(r"\]\((https?://[^)]+)\)", label)
        plain = re.sub(r"\]\((https?://[^)]+)\)", "]", label).replace("[", "").replace("]", "")
        m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", plain.strip())
        if not m:
            continue
        strategy, model = m.group(1).strip(), m.group(2).strip()
        strategy_key = re.sub(r"[^a-z]", "", strategy.lower())
        system = TAU_STRATEGY_NAMES.get(strategy_key, f"tau-bench reference agent ({strategy})")
        scores = {header[i]: cells[i] for i in range(1, min(len(cells), len(header)))}
        pass1 = to_float(scores.get("Pass^1", "").replace("*", ""))
        entries.append(
            Entry(
                family="tau-bench",
                split=domain.lower(),
                system=system,
                model=model,
                score=round(100 * pass1, 1) if pass1 is not None and pass1 <= 1 else pass1,
                metric="pass^1 %",
                date=None,
                url=link.group(1) if link else "https://github.com/sierra-research/tau-bench",
                raw_name=label,
                extra={"strategy": strategy, "pass_k_raw": {k: v.replace("*", "") for k, v in scores.items()}},
            )
        )
    notes["tau_bench"] = {"source": TAU_README, "rows": len(entries)}
    return entries


def harvest_tau2_bench(client: HttpClient, log: logging.Logger, notes: dict[str, Any]) -> list[Entry]:
    manifest = client.get_json(f"{TAU2_S3}/manifest.json")
    entries: list[Entry] = []
    counts: dict[str, int] = {}
    failures: list[str] = []
    for key, modality in (("submissions", "text"), ("legacy_submissions", "text-legacy"), ("voice_submissions", "voice")):
        n = 0
        for d in manifest.get(key, []):
            try:
                sub = client.get_json(f"{TAU2_S3}/{d}/submission.json")
            except HttpError as exc:
                failures.append(f"{d}: {exc}"[:160])
                continue
            model = clean(sub.get("model_name"))
            sub_type = sub.get("submission_type") or "standard"
            org = clean(sub.get("submitting_organization")) or None
            if sub_type == "custom":
                system = f"{model} ({org})" if org else model
            elif modality == "voice":
                system = "tau2-bench reference agent (tau-voice)"
            else:
                system = "tau2-bench reference agent"
            refs = sub.get("references") or []
            ref_url = next((r.get("url") for r in refs if isinstance(r, dict) and r.get("url")), None) if refs else None
            url = ref_url or f"{TAU2_S3}/{d}/submission.json"
            for domain, res in (sub.get("results") or {}).items():
                if not isinstance(res, dict):
                    continue
                entries.append(
                    Entry(
                        family="tau2-bench",
                        split=f"{modality}/{domain}",
                        system=system,
                        model=model,
                        score=to_float(res.get("pass_1")),
                        metric="pass^1 %",
                        date=iso_date(sub.get("submission_date")),
                        url=url,
                        org=org,
                        raw_name=f"{model} [{d}]",
                        extra={
                            "submission_dir": d,
                            "submission_type": sub_type,
                            "pass_2": res.get("pass_2"),
                            "pass_3": res.get("pass_3"),
                            "pass_4": res.get("pass_4"),
                            "cost": res.get("cost"),
                            "model_organization": sub.get("model_organization"),
                            "reasoning_effort": sub.get("reasoning_effort"),
                            "user_simulator": (sub.get("methodology") or {}).get("user_simulator"),
                            "tau2_bench_version": (sub.get("methodology") or {}).get("tau2_bench_version"),
                        },
                    )
                )
            n += 1
        counts[key] = n
    notes["tau2_bench"] = {"source": f"{TAU2_S3}/manifest.json + <dir>/submission.json (linked from taubench.com)", "submissions": counts, "failures": failures}
    return entries


HARVESTERS = {
    "swebench": harvest_swebench,
    "hal": harvest_hal,
    "osworld": harvest_osworld,
    "webarena": harvest_webarena,
    "terminal_bench": harvest_terminal_bench,
    "gaia": harvest_gaia,
    "tau_bench": harvest_tau_bench,
    "tau2_bench": harvest_tau2_bench,
}


# --------------------------------------------------------------------------------------
# grouping into records
# --------------------------------------------------------------------------------------


def build_records(entries: list[Entry], retrieved_at: str) -> list[Record]:
    groups: dict[tuple[str, str], list[Entry]] = defaultdict(list)
    seen: set[tuple[Any, ...]] = set()
    for e in entries:
        key = (e.family, e.split, normalize_title(e.system), e.model, e.score, e.date, e.raw_name)
        if key in seen:
            continue
        seen.add(key)
        groups[(e.family, normalize_title(e.system))].append(e)
    records: list[Record] = []
    for (family, _), items in groups.items():
        items.sort(key=lambda e: ((e.date or "9999"), -(e.score or 0)))
        system = items[0].system
        dates = sorted(d for d in (e.date or "" for e in items) if d)
        urls = [e.url for e in items if e.url]
        orgs = sorted({e.org for e in items if e.org})
        splits = sorted({e.split for e in items})
        seen_lines = []
        for e in items:
            score = f"{e.score:g}" if e.score is not None else "n/a"
            seen_lines.append(f"{e.model or 'model n/a'}: {score} {e.metric} [{e.split}{', ' + e.date if e.date else ''}]")
        seen = "; ".join(seen_lines)
        if len(seen) > 2500:
            seen = seen[:2500] + " ..."
        abstract = f"{DESCRIPTIONS.get(family, family)}. {len(items)} entr{'y' if len(items) == 1 else 'ies'} on {family}. Models and scores seen: {seen}"
        records.append(
            Record(
                id=f"leaderboard:{slug(family)}:{slug(system)}",
                source="leaderboard",
                source_id=f"{slug(family)}/{slug(system)}",
                title=system,
                abstract=abstract,
                authors=orgs,
                date=dates[0] if dates else None,
                venue=family,
                url=urls[0] if urls else None,
                categories=splits,
                query_used=family,
                retrieved_at=retrieved_at,
                extra={"benchmark": family, "n_entries": len(items), "splits": splits, "entries": [e.to_dict() for e in items]},
            )
        )
    records.sort(key=lambda r: (r.query_used, r.title.lower()))
    return records


def main(argv: list[str] | None = None) -> int:
    parser = build_parser("leaderboards", "Harvest agent leaderboards into one record per system.")
    parser.add_argument("--only", default="", help="comma-separated subset of: " + ",".join(HARVESTERS))
    args = parser.parse_args(argv)
    log = setup_logging(args.log_level)
    wanted = [k.strip() for k in args.only.split(",") if k.strip()] or list(HARVESTERS)
    unknown = [k for k in wanted if k not in HARVESTERS]
    if unknown:
        parser.error(f"unknown leaderboard(s): {unknown}")

    client = HttpClient(min_interval=0.4, max_retries=4, timeout=60, logger=log)
    notes: dict[str, Any] = {}
    per_source: dict[str, dict[str, Any]] = {}
    all_entries: list[Entry] = []
    failed: dict[str, str] = {}
    for key in wanted:
        log.info("=== %s", key)
        try:
            entries = HARVESTERS[key](client, log, notes)
        except Exception as exc:  # noqa: BLE001
            log.error("%s failed: %s", key, exc)
            failed[key] = str(exc)[:300]
            entries = []
        systems = {(e.family, normalize_title(e.system)) for e in entries}
        per_source[key] = {"entries": len(entries), "systems": len(systems)}
        log.info("%s: %d entries, %d distinct systems", key, len(entries), len(systems))
        all_entries.extend(entries)

    retrieved_at = now_iso()
    records = build_records(all_entries, retrieved_at)
    if args.max_records and len(records) > args.max_records:
        log.warning("capping %d records to --max-records %d", len(records), args.max_records)
        records = records[: args.max_records]
    written = 0
    with JsonlWriter(args.out, count_only=args.count_only) as w:
        for rec in records:
            if w.write(rec):
                written += 1
    summary = {
        "per_leaderboard": per_source,
        "entries_total": len(all_entries),
        "records": written,
        "count_only": args.count_only,
        "out": None if args.count_only else str(Path(args.out)),
        "failed": failed,
        "notes": notes,
        "http_requests": client.requests_made,
    }
    print_summary("leaderboard", summary)
    return 1 if failed and not per_source else 0


if __name__ == "__main__":
    sys.exit(main())
