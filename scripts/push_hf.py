"""Push a built dataset release to the Hugging Face Hub.

    python scripts/release_dataset.py --version 1.0.0 --out release/
    python scripts/push_hf.py --repo harness-db/harness-db --release release/harness-db-1.0.0 [--dry-run]

The release directory's README.md is the dataset card (YAML front matter with ``configs``), so the
upload is a complete dataset repository. The token is read from ``HF_TOKEN`` in the environment or
``.env``; it is never printed. Every upload is one commit, tagged with the release version, so the
Hub's revision history matches the Zenodo versions.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _token() -> str | None:
    tok = os.environ.get("HF_TOKEN")
    if tok:
        return tok
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="Hub dataset id, e.g. harness-db/harness-db")
    ap.add_argument("--release", required=True, help="built release directory (has VERSION and README.md)")
    ap.add_argument("--private", action="store_true", help="create the Hub repo private")
    ap.add_argument("--dry-run", action="store_true", help="list what would be uploaded and stop")
    a = ap.parse_args(argv)

    rel = pathlib.Path(a.release).resolve()
    version_file = rel / "VERSION"
    card = rel / "README.md"
    if not version_file.exists() or not card.exists():
        print(f"not a release directory (VERSION or README.md missing): {rel}", file=sys.stderr)
        return 2
    version = version_file.read_text(encoding="utf-8").strip()
    if not card.read_text(encoding="utf-8").startswith("---"):
        print("README.md has no YAML front matter; it is not a dataset card", file=sys.stderr)
        return 2

    files = sorted(p for p in rel.rglob("*") if p.is_file())
    print(f"release {version}: {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB")
    for p in files:
        print("  ", p.relative_to(rel).as_posix())
    if a.dry_run:
        return 0

    tok = _token()
    if not tok:
        print("HF_TOKEN not set (environment or .env); nothing uploaded", file=sys.stderr)
        return 3

    from huggingface_hub import HfApi
    from huggingface_hub.errors import HfHubHTTPError

    api = HfApi(token=tok)
    api.create_repo(a.repo, repo_type="dataset", private=a.private, exist_ok=True)
    api.upload_folder(
        repo_id=a.repo,
        repo_type="dataset",
        folder_path=str(rel),
        commit_message=f"HARNESS-DB {version}",
    )
    try:
        api.create_tag(a.repo, tag=f"v{version}", repo_type="dataset", tag_message=f"HARNESS-DB {version}")
    except HfHubHTTPError as exc:  # tag may already exist on a re-push
        print(f"tag v{version} not created: {exc}", file=sys.stderr)
    print(f"uploaded to https://huggingface.co/datasets/{a.repo} (tag v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
