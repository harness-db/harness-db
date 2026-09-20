"""File a registration update (schema response) on the OSF registration, for approval by the admin.

Protocol amendments only count as registered once they are on the OSF record, and OSF allows exactly
one pending update at a time: a PATCH against an unapproved response returns 409, so an update filed
while another is pending is silently lost. This script therefore checks the state of every existing
response first, creates a new revision, writes only the answers that change, and submits it. It never
approves: approval is the author's sign-off on a public research record, and arrives as an OSF email.

The answers come from a JSON file whose keys are OSF question ids (for example "376-50"), plus
`_justification` for the revision justification; `_comment` and any other underscore key are ignored.
Question ids and their current text can be listed with --show.

Usage:
    python scripts/osf_update.py --show
    python scripts/osf_update.py --responses data/osf/update2_responses.json [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API = "https://api.osf.io/v2"
REGISTRATION = "ab2wn"


def env_token() -> str:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OSF_TOKEN="):
            return line.split("=", 1)[1].strip()
    if (tok := os.environ.get("OSF_TOKEN")):
        return tok
    raise SystemExit("OSF_TOKEN not found in .env or the environment")


def call(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/vnd.api+json")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:600]
        raise SystemExit(f"{method} {url} -> HTTP {exc.code}\n{detail}") from exc


def responses(token: str) -> list[dict]:
    out, url = [], f"{API}/registrations/{REGISTRATION}/schema_responses/"
    while url:
        page = call("GET", url, token)
        out.extend(page.get("data", []))
        url = (page.get("links") or {}).get("next")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--responses", type=Path, default=REPO / "data" / "osf" / "update2_responses.json")
    p.add_argument("--show", action="store_true", help="list question ids with their current answers and exit")
    p.add_argument("--dry-run", action="store_true", help="report what would change without filing")
    args = p.parse_args(argv)
    token = env_token()

    existing = responses(token)
    if not existing:
        raise SystemExit("no schema responses on the registration; nothing to revise")
    # Diff against the newest APPROVED response, never against a draft: a draft already carries the
    # answers this script wrote on an earlier attempt, so diffing against it would report nothing to
    # do and skip the submit that the draft is still waiting for.
    approved = [r for r in existing if r["attributes"].get("reviews_state") == "approved"]
    if not approved:
        raise SystemExit("no approved response to revise from")
    current = approved[0]["attributes"].get("revision_responses") or {}

    if args.show:
        for k, v in current.items():
            s = v if isinstance(v, str) else json.dumps(v)
            print(f"{k:10} {len(s):6} chars  {s[:90]!r}")
        return 0

    # OSF allows one pending update at a time, but the two pending states mean different things:
    # `in_progress` is a draft this script created and can finish (writing the answers again is
    # idempotent), while `unapproved` is already submitted and waiting on the author.
    submitted = [r for r in existing if r["attributes"].get("reviews_state") == "unapproved"]
    if submitted:
        for r in submitted:
            print(f"revision {r['id']} is already submitted and waiting for approval")
        raise SystemExit(f"approve or withdraw it at https://osf.io/{REGISTRATION}/ before filing another")
    draft = next((r for r in existing if r["attributes"].get("reviews_state") == "in_progress"), None)

    spec = json.loads(args.responses.read_text(encoding="utf-8"))
    justification = spec.get("_justification", "").strip()
    answers = {k: v for k, v in spec.items() if not k.startswith("_")}
    if not justification:
        raise SystemExit(f"{args.responses} has no _justification")

    unknown = [k for k in answers if k not in current]
    if unknown:
        raise SystemExit(f"these keys are not questions on this registration: {unknown}")
    changed = {k: v for k, v in answers.items() if current.get(k) != v}
    print(f"{len(answers)} answers supplied, {len(changed)} differ from the live record:")
    for k in changed:
        print(f"  {k:10} {len(str(current.get(k, ''))):6} -> {len(str(changed[k])):6} chars")
    print(f"justification: {len(justification)} chars")
    if not changed:
        print("nothing to file")
        return 0
    if args.dry_run:
        print("\ndry run: nothing filed")
        return 0

    if draft is not None:
        rid = draft["id"]
        print(f"\nresuming the draft revision {rid} left in progress")
    else:
        # A new revision is created on the schema_responses collection with a relationship to the
        # registration; the registration's own sub-collection is read-only (POST there returns 405).
        created = call("POST", f"{API}/schema_responses/", token,
                       {"data": {"type": "schema-responses",
                                 "relationships": {"registration": {
                                     "data": {"id": REGISTRATION, "type": "registrations"}}}}})
        rid = created["data"]["id"]
        print(f"\ncreated revision {rid}")

    call("PATCH", f"{API}/schema_responses/{rid}/", token,
         {"data": {"id": rid, "type": "schema-responses",
                   "attributes": {"revision_responses": {**current, **changed},
                                  "revision_justification": justification}}})
    print(f"wrote {len(changed)} revised answers")

    # The action must name the revision it acts on: without relationships.target OSF returns 400.
    call("POST", f"{API}/schema_responses/{rid}/actions/", token,
         {"data": {"type": "schema-response-actions",
                   "attributes": {"trigger": "submit",
                                  "comment": "Amendments 2-8; see the revision justification."},
                   "relationships": {"target": {
                       "data": {"id": rid, "type": "schema-responses"}}}}})
    print("submitted for approval")
    print(f"\nAPPROVE IT HERE: https://osf.io/{REGISTRATION}/ (an OSF email also carries the link)")
    print("Until it is approved the amendments are not on the public record.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
