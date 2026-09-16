"""Harvest OpenReview submissions (ICLR 2023-2026, NeurIPS 2023-2025, ICML 2023-2026).

API v2: https://api2.openreview.net/notes with ``invitation=<venue>/-/Submission`` (all
submissions, accepted or not) and, as a fallback for accepted-only, ``content.venueid``.
ICLR 2023 and ICML 2023 live on API v1 (https://api.openreview.net) under
``<venue>/-/Blind_Submission`` / ``<venue>/-/Submission``; both APIs are tried in order.
Results are filtered locally: title + abstract must match the harness block AND the LLM
block (case-insensitive regexes from ``common.py``).

Access. As of 2026-09 both OpenReview APIs answer unauthenticated requests with
``403 ChallengeRequiredError`` (a Cloudflare Turnstile browser challenge) or ``429`` from
nginx. The script therefore logs in when ``OPENREVIEW_USERNAME`` and ``OPENREVIEW_PASSWORD``
are set (environment or the repo's ``.env``) via ``POST /login`` and sends the returned
bearer token. Without credentials it records the failure per venue and exits non-zero;
it never fabricates counts.

``--discover`` prints the invitations/groups found for each venue (``GET /invitations``
with ``prefix=<venue>/-/``) to help confirm the invitation ids.

Usage:
    python scripts/harvest/openreview.py --since 2022-10-01 --until 2026-08-31 \
        --out data/raw/openreview.jsonl [--count-only] [--discover]
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import (
    HARNESS_TERMS,
    LLM_TERMS,
    REPO_ROOT,
    STRONG_TERMS,
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    matches_blocks,
    normalize_arxiv_id,
    now_iso,
    print_summary,
    setup_logging,
)

API_V2 = "https://api2.openreview.net"
API_V1 = "https://api.openreview.net"
PAGE = 1000
MIN_INTERVAL = 1.0


@dataclass(frozen=True)
class Venue:
    group: str  # e.g. ICLR.cc/2024/Conference
    year: int
    apis: tuple[str, ...]  # order in which to try base URLs

    @property
    def invitations(self) -> tuple[str, ...]:
        return (f"{self.group}/-/Submission", f"{self.group}/-/Blind_Submission")


def default_venues() -> list[Venue]:
    venues: list[Venue] = []
    for y in range(2023, 2027):
        venues.append(Venue(f"ICLR.cc/{y}/Conference", y, (API_V2, API_V1) if y >= 2024 else (API_V1, API_V2)))
    for y in range(2023, 2026):
        venues.append(Venue(f"NeurIPS.cc/{y}/Conference", y, (API_V2, API_V1)))
    for y in range(2023, 2027):
        venues.append(Venue(f"ICML.cc/{y}/Conference", y, (API_V2, API_V1) if y >= 2024 else (API_V1, API_V2)))
    return venues


# --------------------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------------------


def load_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def credentials() -> tuple[str, str] | None:
    env = {**load_dotenv(REPO_ROOT / ".env"), **os.environ}
    user, pw = env.get("OPENREVIEW_USERNAME"), env.get("OPENREVIEW_PASSWORD")
    return (user, pw) if user and pw else None


def login(client: HttpClient, base: str, creds: tuple[str, str], log: logging.Logger) -> str | None:
    resp = client.request("POST", f"{base}/login", json_body={"id": creds[0], "password": creds[1]})
    if resp.status_code != 200:
        log.error("login to %s failed: HTTP %s %s", base, resp.status_code, resp.text[:200])
        return None
    return resp.json().get("token")


# --------------------------------------------------------------------------------------
# Notes
# --------------------------------------------------------------------------------------


def _val(content: dict[str, Any], key: str) -> Any:
    v = content.get(key)
    if isinstance(v, dict) and "value" in v:  # API v2 shape
        return v["value"]
    return v


class ChallengeRequired(HttpError):
    pass


def fetch_notes(client: HttpClient, base: str, params: dict[str, Any], token: str | None) -> Iterator[tuple[int, dict[str, Any]]]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    offset = 0
    while True:
        resp = client.get(f"{base}/notes", params={**params, "limit": PAGE, "offset": offset}, headers=headers)
        if resp.status_code == 403 and "Challenge" in resp.text:
            raise ChallengeRequired(f"{base}: {resp.text[:160]}")
        if resp.status_code != 200:
            raise HttpError(f"{base}/notes HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        notes = data.get("notes", [])
        count = int(data.get("count", len(notes)))
        for n in notes:
            yield count, n
        offset += len(notes)
        if not notes or offset >= count:
            break


def note_to_record(note: dict[str, Any], venue: Venue, query: str) -> Record:
    c = note.get("content") or {}
    title = str(_val(c, "title") or "").strip()
    abstract = str(_val(c, "abstract") or "").strip()
    authors = _val(c, "authors") or []
    venueid = _val(c, "venueid") or ""
    venue_name = _val(c, "venue") or venue.group
    pdf = _val(c, "pdf")
    ts = note.get("pdate") or note.get("cdate") or note.get("tcdate")
    date = None
    if isinstance(ts, (int, float)):
        from datetime import UTC, datetime

        date = datetime.fromtimestamp(ts / 1000, UTC).strftime("%Y-%m-%d")
    return Record(
        id=f"openreview:{note['id']}",
        source="openreview",
        source_id=note["id"],
        title=title,
        abstract=abstract,
        authors=[str(a) for a in authors],
        date=date or str(venue.year),
        venue=str(venue_name),
        url=f"https://openreview.net/forum?id={note['id']}",
        doi=None,
        arxiv_id=normalize_arxiv_id(str(_val(c, "_bibtex") or "")) ,
        categories=[venue.group],
        query_used=query,
        retrieved_at=now_iso(),
        extra={"venueid": venueid, "pdf": pdf, "invitation": note.get("invitation") or (note.get("invitations") or [None])[0]},
    )


def harvest_venue(
    client: HttpClient, venue: Venue, tokens: dict[str, str | None], log: logging.Logger
) -> tuple[str | None, int, list[dict[str, Any]], str | None]:
    """Return (invitation_used, total_submissions, notes, error)."""
    last_err: str | None = None
    for base in venue.apis:
        for inv in venue.invitations:
            try:
                notes: list[dict[str, Any]] = []
                total = 0
                for total, n in fetch_notes(client, base, {"invitation": inv}, tokens.get(base)):
                    notes.append(n)
                if total > 0:
                    log.info("%s: %d submissions via %s (%s)", venue.group, total, inv, base)
                    return inv, total, notes, None
            except ChallengeRequired as exc:
                last_err = f"challenge required: {exc}"
                log.error("%s: %s", venue.group, last_err)
                break  # no point trying other invitations on this API
            except HttpError as exc:
                last_err = str(exc)
                log.warning("%s: %s", venue.group, last_err)
    return None, 0, [], last_err or "no submissions found under any known invitation"


def discover(client: HttpClient, venue: Venue, tokens: dict[str, str | None], log: logging.Logger) -> None:
    for base in venue.apis:
        headers = {"Authorization": f"Bearer {tokens[base]}"} if tokens.get(base) else {}
        resp = client.get(f"{base}/invitations", params={"prefix": f"{venue.group}/-/", "limit": 50}, headers=headers)
        log.info("%s %s/invitations -> HTTP %s", venue.group, base, resp.status_code)
        if resp.status_code == 200:
            for inv in resp.json().get("invitations", []):
                print(f"  {base}  {inv.get('id')}")


def main(argv: list[str] | None = None) -> int:
    p = build_parser("openreview", __doc__.split("\n\n")[0])
    p.add_argument("--discover", action="store_true", help="list invitations per venue and exit")
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=MIN_INTERVAL, max_retries=3, logger=log)
    query = f"regex(title+abstract) harness={list(HARNESS_TERMS)} AND llm={list(LLM_TERMS)}"
    if args.waive_llm_on_strong:
        query += f" OR strong={list(STRONG_TERMS)}"

    creds = credentials()
    tokens: dict[str, str | None] = {}
    if creds:
        for base in (API_V2, API_V1):
            tokens[base] = login(client, base, creds, log)
    else:
        log.warning("no OPENREVIEW_USERNAME/OPENREVIEW_PASSWORD set; trying unauthenticated")

    venues = default_venues()
    if args.discover:
        for v in venues:
            discover(client, v, tokens, log)
        return 0

    per_venue: dict[str, dict[str, Any]] = {}
    written = 0
    capped = False
    with JsonlWriter(args.out, count_only=args.count_only) as w:
        for v in venues:
            inv, total, notes, err = harvest_venue(client, v, tokens, log)
            matched = 0
            strong_added = 0
            for n in notes:
                c = n.get("content") or {}
                text = f"{_val(c, 'title') or ''}\n{_val(c, 'abstract') or ''}"
                if matches_blocks(text, waive_llm_on_strong=args.waive_llm_on_strong):
                    matched += 1
                    if not matches_blocks(text):
                        strong_added += 1
                    if args.max_records and w.count >= args.max_records:
                        capped = True
                        continue
                    w.write(note_to_record(n, v, query))
            per_venue[v.group] = {"invitation": inv, "submissions": total, "matched": matched, "strong_added": strong_added, "error": err}
        written = w.count
    failed = [g for g, r in per_venue.items() if r["error"]]
    print_summary(
        "openreview",
        {
            "query": query,
            "venues": per_venue,
            "counts": {"both": sum(r["matched"] for r in per_venue.values())},
            "written": written,
            "capped": capped,
            "max_records": args.max_records,
            "waive_llm_on_strong": args.waive_llm_on_strong,
            "error": f"{len(failed)}/{len(per_venue)} venues failed: {failed[0] if failed else ''} ... ({per_venue[failed[0]]['error'] if failed else ''})" if failed else None,
            "requests": client.requests_made,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
