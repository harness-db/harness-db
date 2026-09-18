# scripts/

| Script | Task | Status |
|---|---|---|
| `build_schema.py` | Generate `schema/harness_db.schema.json` from `schema/dimensions.json` | done |
| `validate.py` | Schema, referential integrity, evidence-per-cell checks (runs in CI) | done |
| `kappa.py` | Cohen's kappa for screening votes and per-dimension coding | done |
| `harvest/arxiv.py`, `harvest/s2.py`, `harvest/openalex.py`, `harvest/acl.py`, `harvest/openreview.py`, `harvest/github.py` | Source harvesting to `data/raw/*.jsonl` (see `harvest/README.md`) | done |
| `dedupe.py` | Merge harvests into `data/raw/candidates.csv` with per-source counts | done |
| `screen_llm.py` | LLM screening votes to `data/screening/llm_votes.csv`; `--mode tiebreak` writes the decisive third vote to `llm_votes_tiebreak.csv` | S2 |
| `prisma_diagram.py` | PRISMA 2020 flow diagram from `data/prisma_counts.json` | S2 |
| `prefill/llm_code_system.py` | Pre-fill coding cells with evidence from paper + repo | S3 |
| `analysis/descriptives.py`, `analysis/cooccurrence.py`, `analysis/regression.py`, `analysis/figures.py` | Synthesis and figures | S4 |
