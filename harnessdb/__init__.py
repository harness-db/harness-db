"""harnessdb: load HARNESS-DB, the coded dataset of LLM agent harnesses, into pandas.

>>> import harnessdb as hdb
>>> db = hdb.load()                          # repo data/, a release directory, or a path
>>> db.systems                               # one row per system (metadata, stratum, weight)
>>> db.cells                                 # one row per system x dimension, with evidence
>>> db.wide()                                # one row per system, one column per dimension
>>> db.dimension("self_verification")        # value distribution, unweighted and weighted
>>> db.not_reported(by="layer")              # under-reporting rates with design SEs
>>> db.evidence("openhands", "self_verification")

Three rules hold for everything the loader returns or computes:

1. ``not_reported`` is documented silence, never absence. Such a cell has ``value = None`` and is
   never mapped to a value (the schema's ``"none"`` is a coded finding, not silence).
2. ``unresolved`` (cells that failed release validation) is excluded from every rate.
3. Weighted estimates use only weight-bearing systems; the 23 systems at weight 0, coded outside
   the drawn sample, are out-of-sample and enter unweighted numbers only.

Multi-valued dimensions are Python lists in ``db.cells`` and pipe-joined strings in ``db.wide()``
(``db.wide(multi="list")`` keeps lists). Run ``python -m harnessdb --summary`` for the counts.
"""

from __future__ import annotations

from ._locate import ENV_VAR, Sources, locate
from .core import (
    CODED,
    NOT_REPORTED,
    STATES,
    UNRESOLVED,
    DimensionSummary,
    Evidence,
    HarnessDB,
    cell_state,
    load,
    split_evidence,
)
from .schema import Schema

#: Version of the loader package (the ``harness-db`` distribution).
__version__ = "0.1.0"

__all__ = [
    "CODED", "ENV_VAR", "NOT_REPORTED", "STATES", "UNRESOLVED", "DimensionSummary", "Evidence",
    "HarnessDB", "Schema", "Sources", "__version__", "cell_state", "load", "locate",
    "split_evidence",
]
