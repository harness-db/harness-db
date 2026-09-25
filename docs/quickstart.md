# HARNESS-DB from Python: quickstart

The `harnessdb` package loads the dataset into pandas. It reads either the in-repo `data/` directory or a
packaged release, which it reads through the release's `datapackage.json`. It needs only pandas and the standard
library.

```bash
pip install -e .                  # from a checkout: installs the harness-db distribution, including harnessdb
pip install -e ".[hf]"            # plus Hugging Face `datasets`, for db.to_hf()
pip install pyarrow               # only for a release shipped as Parquet
python -m harnessdb --summary     # the counts to check against the paper
```

```python
import harnessdb as hdb
db = hdb.load()                                  # finds data/ in this checkout
db = hdb.load("release/harness-db-1.0.0")        # a built release (reads its datapackage.json)
db = hdb.load("path/to/datapackage.json")        # or the descriptor itself
# or set HARNESSDB_DATA=/path/to/release and call hdb.load()
```

The release and the in-repo data load to identical `systems` and `cells`. The test suite checks this whenever a
release has been built under `release/`. From a release, the loader reads the nested `data/systems.json` for the
cells, `data/systems_wide.csv` for each system's `stratum` and `weight`, and `data/cells.csv` for the validation
flags. A release that ships only `systems_wide.csv` and `cells.csv` also loads. The loader rebuilds the cells from
those two files.

In a checkout, `python -m harnessdb --summary` prints:

```
HARNESS-DB  (harnessdb 0.1.0, schema 1.0.0)
source                  repo:C:\Users\Bhaskar\Pictures\Research\harness-db\data

systems                   1,256
cells                    47,728   (1,256 systems x 38 dimensions in 9 layers)
  coded                  24,228   50.8%   (value + evidence)
  not_reported           23,337   48.9%   (documented silence, never a value)
  unresolved                163    0.3%   (excluded from every rate)

strata in the release   H 983 / P 157 / O 116
sampling frame          6,504 systems (H 984 / P 683 / O 4,837)
weight-bearing systems    1,233   (every weighted estimate rests on these)
weight 0 (out-of-sample)     23   (unweighted statements only)

results                   5,863 score rows, 646 systems, 1,138 benchmark names
```

Every number in this printout is one the manuscript states. The summary prints counts only, never an estimate.
`python -m harnessdb --json` prints the same counts as JSON, and `--data PATH` points it at a release.

## Three rules

The loader follows three rules in everything it returns or computes. Follow them in your own code too.

1. **`not_reported` means the sources are silent. It does not mean the feature is absent.** A `not_reported` cell has
   `value = None`, and the loader never turns it into a value. In particular it is not the schema's `"none"`:
   `"none"` is a coded finding, backed by evidence, that the harness has no such mechanism.
2. **`unresolved` is left out of every rate.** These are the 163 cells that failed release validation. They stay in
   `db.cells` and are counted in `n_unresolved` columns, but they appear in no numerator and no denominator.
3. **Weighted estimates use only weight-bearing systems.** The 23 systems coded outside the drawn sample
   (benchmark reference agents and similar) have `weight = 0`. They count in every unweighted number and in no
   weighted number or design SE. Weighted numbers estimate the 6,504-system field. Unweighted numbers describe the
   1,256 coded systems.

## What is in `db`

| attribute / method | what it returns |
|---|---|
| `db.systems` | one row per system: `system_id, name, version_label, repo_url, aliases, papers, coded_at, notes, stratum, weight, weight_bearing, n_coded, n_not_reported, n_unresolved` |
| `db.cells` | one row per system x dimension (47,728): `system_id, layer, dimension_key, state, value, quote, locator, confidence, dimension_id, multi, evidence, coder, note, validation_flags` |
| `db.wide(multi="join", sep="\|")` | one row per system: `system_id, name, stratum, weight`, one value column per dimension, then one `<key>__state` column per dimension |
| `db.dimension(key)` | a `DimensionSummary`: value distribution (unweighted and weighted, with design SEs) and the coded / not_reported / unresolved counts |
| `db.not_reported(by="layer")` | under-reporting rates by `"layer"`, `"dimension"`, `"stratum"` or `None`, unweighted and weighted, with design SEs |
| `db.evidence(system, dimension=None)` | an `Evidence` record (quote, locator, value, state, confidence, note) for one cell, or a system's 38 cells as a DataFrame |
| `db.results` | reported scores (`system_id, model, benchmark, split, metric, score, cost_usd, tokens, ..., comparable_key`) |
| `db.papers` | bibliographic rows, included and excluded (`included` is boolean) |
| `db.schema` | the parsed `dimensions.json`: `db.schema.values("loop_primitives")`, `.dimension("E1")`, `.is_multi(k)`, `.layers`, `.table` |
| `db.to_hf()` | a `datasets.DatasetDict` with `systems` and `cells` splits (needs the `[hf]` extra) |
| `db.summary()` | the headline counts as a dict |

**How values are stored.** In `db.cells`, a multi-valued dimension's `value` is a Python **list**, such as
`["multi_attempt", "react"]`. `tool_count` and `stars` are `int`s, and every other value is a string. In
`db.wide()`, multi-valued dimensions are **pipe-joined strings** in the dataset's sorted order, such as
`"multi_attempt|react"`. Pass `db.wide(multi="list")` to keep them as lists. `db.cells.explode("value")` gives one row
per value. A missing value in `wide()` can mean `not_reported` or `unresolved`, so check the `__state` column to see
which.

**Design SEs.** A weighted rate is `sum(w * flag) / sum(w)` over weight-bearing systems. The strata are H with
weight 1, P with weight 4.5533 and O with weight 48.37. The standard error is stratified and design-based: a Taylor
linearisation of the ratio with a finite-population correction, and with each **system** as the sampling unit,
because systems are what was drawn. When a layer pools 3 to 7 cells per system, those cells are treated as one
cluster, not as independent draws. This is the manuscript's estimator (`weighted_share` in
`scripts/analyse_descriptives.py`). So `db.not_reported(by="dimension")`, `db.not_reported(by="layer")` and
`db.dimension(k)` reproduce `data/analysis/under_reporting_by_dimension.csv`, `summary_one_screen.csv` and
`value_distributions.csv` to 1e-9, and the test suite checks all three.

## (a) Which harnesses run tests as self-verification?

```python
sv = db.dimension("self_verification")
print(sv)
```

```
E1 self_verification (layer E, enum, multi-valued): 1256 systems = 644 coded + 608 not_reported + 4 unresolved
not_reported rate (unresolved excluded): 48.6% unweighted, 39.4% weighted (SE 3.6 pts)
            value  n_systems  share_unweighted  weight_systems  share_weighted  se_weighted
             none         53          0.082298         72.3198        0.018522     0.002854
    self_critique        156          0.242236        837.6989        0.214547     0.037741
   test_execution        211          0.327640       1642.9590        0.420786     0.047371
linters_typecheck         69          0.107143        228.8765        0.058619     0.020494
        llm_judge        317          0.492236       1581.9054        0.405149     0.046412
           formal         13          0.020186        169.3232        0.043366     0.020409
```

The shares are over the 644 systems that report their self-verification. The dimension is multi-valued, so a system
counts once for each value it uses and the shares add up to more than 1. The 608 silent systems are not in any
share. Silence is not "none". Now list the harnesses:

```python
w = db.wide()
tests = w[w["self_verification"].str.contains("test_execution", na=False)]
print(len(tests))
print(tests.nlargest(8, "stars")[["name", "self_verification", "stars"]].to_string(index=False))
```

```
211
                      name                          self_verification  stars
MetaGPT (software company)                             test_execution  70499
                 DeepTutor                   llm_judge|test_execution  39997
               Prime Agent                             test_execution  21061
                  DeepCode                             test_execution  16576
                 R&D-Agent                   llm_judge|test_execution  14683
           ComfyUI-Copilot                             test_execution   5520
             AutoCodeRover                   llm_judge|test_execution   3099
               Paper2Agent linters_typecheck|llm_judge|test_execution   3087
```

`test_execution` is not a substring of any other value, so `str.contains` on the joined column is safe here. For a
general test, use `db.wide(multi="list")` and `lambda v: isinstance(v, list) and "x" in v`.

## (b) The under-reporting gradient by layer

```python
lay = db.not_reported(by="layer").sort_values("rate_weighted")
print(lay[["layer", "layer_name", "n_base", "rate_unweighted", "rate_weighted", "se_weighted"]]
      .round(3).to_string(index=False))
```

```
layer                   layer_name  n_base  rate_unweighted  rate_weighted  se_weighted
    C                 Control loop    6250            0.271          0.249        0.012
    M                         Meta    8782            0.274          0.346        0.013
    A             Context assembly    5005            0.444          0.402        0.020
    E      Verification and repair    3761            0.650          0.609        0.023
    D             Memory and state    3751            0.527          0.633        0.021
    F       Budget and termination    3758            0.615          0.651        0.020
    B               Tool interface    6234            0.634          0.714        0.020
    H Observability and governance    5014            0.597          0.728        0.020
    G      Sandbox and environment    5010            0.666          0.816        0.018
```

The weighted rate climbs from 24.9% ± 1.2 for the control loop to 81.6% ± 1.8 for sandbox and environment,
the same numbers as `data/analysis/summary_one_screen.csv`.

Sources describe the control loop and are silent about the sandbox. `n_base` excludes unresolved cells. The weighted
column is the field estimate, and it is higher than the unweighted one for most layers because the less visible
strata document less. For per-dimension rates use `by="dimension"`, and for the overall rate use `by=None`.

## (c) Join scores to design choices for one benchmark

```python
r = db.results
swe = r[(r["benchmark"] == "SWE-bench") & (r["split"] == "Verified")
        & (r["metric"].str.lower() == "% resolved")]
best = swe.groupby("system_id", as_index=False)["score"].max()          # 22 systems, 89 rows
design = db.wide()[["system_id", "name", "loop_primitives", "self_verification",
                    "multi_agent_topology", "self_verification__state"]]
joined = best.merge(design, on="system_id").sort_values("score", ascending=False)
print(joined.drop(columns="self_verification__state").head(8).to_string(index=False))
```

```
      system_id  score            name                                         loop_primitives        self_verification multi_agent_topology
 live-swe-agent   79.2  Live-SWE-agent                                                   react                     None               single
 mini-swe-agent   76.8  mini-swe-agent                                                   react                     None               single
       rovo-dev   76.8        Rovo Dev                                                    None                     None                 None
         acoder   76.4          ACoder                                                    None                     None orchestrator_workers
         lingxi   74.6          Lingxi                                    fixed_pipeline|react                     None             pipeline
        joycode   74.6         JoyCode fixed_pipeline|generate_test_repair|multi_attempt|react llm_judge|test_execution             pipeline
     prometheus   74.4      Prometheus       fixed_pipeline|generate_test_repair|multi_attempt llm_judge|test_execution             pipeline
refact-ai-agent   74.4 Refact.ai Agent                                                   react                     None                 None
```

```python
runs = joined["self_verification"].str.contains("test_execution", na=False)
joined["verification"] = runs.map({True: "test_execution", False: "coded, no tests"})
joined["verification"] = joined["verification"].where(
    joined["self_verification__state"] == "coded", joined["self_verification__state"])
print(joined.groupby("verification")["score"].agg(["count", "median"]).round(1))
```

```
                 count  median
verification
coded, no tests      3    60.4
not_reported        10    74.5
test_execution       9    64.6
```

Ten of the 22 systems say nothing about self-verification, and they have the highest median score. They have to
stay a separate group. Folding them into "no tests" would break rule 1 and would change the comparison. Reported scores differ in model, split and metric, so
this is description and not an effect estimate. For like-for-like rows, group on `comparable_key` (benchmark, split
and model). Benchmark and metric names are as reported (see quirks below).

## (d) Everything one system's cells say, with their evidence

```python
cells = db.evidence("swe-agent")                   # 38 rows, schema order
print(cells["state"].value_counts().to_string())
print(cells[["dimension_key", "state", "value", "locator"]].head(12).to_string(index=False))
```

```
state
not_reported    21
coded           17
unresolved       0
           dimension_key        state                                                         value                                     locator
     system_prompt_style        coded                                                     templated          docs/config/config.md@0f3acafacabc
    env_context_strategy        coded                                       agent_driven_navigation       docs/background/index.md@0f3acafacabc
      context_compaction not_reported                                                          None                                        None
      observation_format        coded                                                    [raw_text]         docs/background/aci.md@0f3acafacabc
        tool_call_format        coded [json_in_text, native_function_calling, shell_only, xml_tags]                    docs/faq.md@0f3acafacabc
              tool_count not_reported                                                          None                                        None
          edit_primitive not_reported                                                          None                                        None
      tool_schema_source        coded                                                [hand_written]          docs/config/config.md@0f3acafacabc
protocol_standardization not_reported                                                          None                                        None
         loop_primitives        coded                                        [multi_attempt, react] docs/reference/agent_config.md@0f3acafacabc
    planning_granularity not_reported                                                          None                                        None
    multi_agent_topology        coded                                                        single docs/reference/agent_config.md@0f3acafacabc
```

```python
print(db.evidence("swe-agent", "loop_primitives"))
print(db.evidence("swe-agent", "E1"))              # ids work as well as keys
print(db.evidence("swe-agent", "edit_primitive"))
```

```
SWE-agent [swe-agent] / C1 loop_primitives
  state:      coded
  value:      ['multi_attempt', 'react']
  confidence: medium
  quote:      `RetryAgentConfig`: A "meta agent" that instantiates multiple agents for multiple attempts and then picks the best solution.
  locator:    docs/reference/agent_config.md@0f3acafacabc
  note:       Default is react via DefaultAgent.
SWE-agent [swe-agent] / E1 self_verification
  state:      coded
  value:      ['linters_typecheck']
  confidence: low
  quote:      We add a **linter** that runs when an edit command is issued, and do not let the edit command go through if the code isn't syntactically correct.
  locator:    docs/background/aci.md@0f3acafacabc
  note:       reviewer.py and review_on_submit are present in the tree but not in the bundle.
SWE-agent [swe-agent] / B3 edit_primitive
  state:      not_reported
  confidence: low
  note:       Tool config files are listed but not included in the bundle.
```

The last cell shows why rule 1 matters. SWE-agent certainly has an edit tool, but the evidence bundle the coders read
did not document it, so the cell records silence and not a value. The `note` says why. `evidence()` accepts a
`system_id`, and falls back to an exact name or alias. An unknown id raises `KeyError` with close matches (for
example `openhand` suggests `openhands`, `openhands-2`, and so on).

## (e) Load into Hugging Face `datasets`

```python
dd = db.to_hf()                 # pip install -e ".[hf]"
print(dd)
coded = dd["cells"].filter(lambda r: r["dimension_key"] == "loop_primitives" and r["state"] == "coded")
print(coded.num_rows, coded[0]["system_id"], coded[0]["value"])
```

```
DatasetDict({
    systems: Dataset({
        features: ['system_id', 'name', 'version_label', 'repo_url', 'aliases', 'papers', 'coded_at', 'notes', 'stratum', 'weight', 'weight_bearing', 'n_coded', 'n_not_reported', 'n_unresolved'],
        num_rows: 1256
    })
    cells: Dataset({
        features: ['system_id', 'layer', 'dimension_key', 'state', 'value', 'quote', 'locator', 'confidence', 'dimension_id', 'multi', 'evidence', 'coder', 'note', 'validation_flags'],
        num_rows: 47728
    })
})
1156 1code ['event_driven', 'plan_execute', 'react']
```

Arrow needs a single type per column, so in the `cells` split `value` is `list<string>` for every dimension. A
single value becomes a one-element list, integers become decimal strings, and the column is **null** (not `[]`) for
`not_reported` and `unresolved` cells. `stratum` and `weight` are in the `systems` split, which joins on
`system_id`. Save with `dd.save_to_disk(...)` or `dd.push_to_hub(...)`.

## Data quirks you will hit

- **Silence is common.** 48.9% of all cells are `not_reported`, including cells for features a system well known to
  have (see SWE-agent's `edit_primitive` above). Coders coded only what the evidence bundle documented. Never treat
  a missing value as "no".
- **`"none"` is a value.** It is a coded, evidenced absence, and it is an allowed value in 21 of the 38 dimensions
  (such as `self_verification`, `rollback` and `network_policy`). It is not silence.
- **Why a cell is unresolved.** Loaded from a release, `validation_flags` gives the reason each of the 163
  `unresolved` cells failed release validation, such as `quote_not_in_bundle`, `locator_no_line` or
  `scalar_for_multi`. The column is `None` for in-repo data, but every unresolved cell's `note` starts with the same
  reasons, for example `unresolved after the repair pass (scalar_for_multi)`.
- **80 `not_reported` cells carry evidence.** Their quote is the passage that stops short of saying. So "has a
  quote" does not imply "coded".
- **58 evidence strings are bare locators** with no quote, such as `README.md@585fe7c`. For these, `quote` is `None`
  and `locator` is set. Every evidence string has a locator. Locators are `path@commit`, `path:line@commit`, or
  `paper Sec. N`, and some contain parentheses of their own, which the parser handles.
- **Four dimensions are not enums.** `tool_count` and `stars` are integers, `first_release_date` is a date string, and
  `pinned_version` is free text. `dimension()` lists their observed values, most frequent first. `first_release_date`
  is coded for only 412 of 1,256 systems.
- **Results are as reported.** The same benchmark can appear under several names (`HotpotQA` and `HotPotQA`, 1,138
  distinct names). Metrics vary in name and scale (`% resolved` and `% Resolved`, `accuracy` and `accuracy %`).
  Only 390 of 5,863 rows carry a `comparable_key`. Filter on benchmark, split and metric before comparing.
- **`papers` depends on the source.** In a checkout it holds the whole screening set (8,538 rows, 7,122 included,
  with `included` and `exclusion_reason`). A release ships the 7,122 included papers only, with a `system_ids`
  column and no `included` column. `db.systems["papers"]` lists the paper ids for each system in both cases.
- **System ids are not names.** Several ids share a family, for example `openhands` (CodeActAgent), `openhands-2`,
  `openhands-3` and `openhands-versa`. One frame-coded system, `con`, is missing from the release, because `con` is a
  reserved file name on Windows. That is why the weights sum to 6,503 and not 6,504. See
  `docs/count_reconciliation.md`.
- **Weighted is not the same as unweighted.** One O-stratum system moves a weighted share by about 0.7 points, so
  always report `se_weighted` next to a weighted rate.
