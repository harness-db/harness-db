# data/

| File | Contents | Edited by |
|---|---|---|
| `systems.json` | One object per harness, coded on every dimension with evidence (validated by `scripts/validate.py`) | coders |
| `papers.csv` | Bibliographic rows for included and excluded papers, with exclusion reasons | screening |
| `results.csv` | Reported scores per system, model, benchmark, split; `comparable_key` groups rows sharing benchmark, split and model | outcomes extraction |
| `prisma_counts.json` | Numbers for the PRISMA 2020 flow diagram | screening |
| `raw/` | Harvested candidates per source (`*.jsonl`) and `candidates.csv` after dedupe. Never edited by hand | scripts |
| `screening/` | Rayyan exports, LLM votes, kappa reports | screening |
| `prefill/` | Subagent pre-fill JSON per system, before human verification | S3 |
