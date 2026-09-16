# Positioning: what HARNESS-Review adds over existing harness surveys

Status: stub. Fill after reading the four competitor surveys in full (tracker task 1).

## Prior work (as of 2026-09-16)

| Work | Coverage | Method | Dataset | Design-to-outcome analysis |
|---|---|---|---|---|
| Agent Harness Engineering: A Survey (Picrew et al., TMLR submission; ETCLOVG 7-layer; H=(E,T,C,S,L,V)) | 110+ papers, 23 systems | Narrative | Completeness matrix; HF dataset of annotated papers | One anecdote |
| From Question Answering to Task Completion (Guo et al., arXiv:2606.20683; 6 runtime responsibilities) | not stated | Narrative | Awesome-list | None |
| Inside the Scaffold (Rombaut, arXiv:2604.03515; 12 dimensions, 3 layers) | 13 coding scaffolds | Source-code case study | In-paper tables | None |
| Harness Engineering as Categorical Architecture (arXiv:2605.12239) | — | Formal | — | — |
| Harness-effect experiments (2605.27922, 2607.22585, 2608.26218, 2608.23953, 2609.17394, 2605.29682) | 2–3 harnesses each | Experiments | — | Yes, tiny N |

## Our four differentiators

1. PRISMA 2020, pre-registered, dual screening, Cohen's kappa per dimension.
2. 150–300 systems on ~38 dimensions with evidence per cell.
3. Corpus-wide quantitative synthesis with benchmark and model held constant.
4. A crosswalk reconciling ETCLOVG-7, Guo-6, H=(E,T,C,S,L,V) and Rombaut-12 into one schema
   (`schema/dimensions.json` carries the layer-level mapping; refine to dimension level here).

## Delta memo (to write)

- What each survey defines a harness as, and where the definitions disagree.
- Which of our 38 dimensions each survey covers, partially covers, or omits.
- Claims in those surveys that our data can test.
