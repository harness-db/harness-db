"""The coding sheet (``schema/dimensions.json``) as a small, read-only object."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import pandas as pd


class Schema(Mapping[str, Any]):
    """The parsed ``dimensions.json``: 9 layers, 38 dimensions, their types and allowed values.

    It behaves as a read-only mapping over the raw JSON (``schema["dimensions"]``,
    ``schema["schema_version"]``), plus helpers:

    >>> schema.values("loop_primitives")          # allowed values, in schema order
    >>> schema.dimension("self_verification")     # one dimension's spec as a dict
    >>> schema.is_multi("self_verification")      # True: the cell holds a list
    >>> schema.table                              # one row per dimension, as a DataFrame

    Note that ``values`` here takes a dimension key and returns that dimension's allowed values; it
    shadows ``Mapping.values()``. Use ``schema.raw.values()`` for the mapping's own values.
    """

    def __init__(self, raw: dict[str, Any]):
        if "dimensions" not in raw or "layers" not in raw:
            raise ValueError("not a HARNESS-DB dimensions.json: needs 'layers' and 'dimensions'")
        self.raw: dict[str, Any] = raw
        self._by_key: dict[str, dict[str, Any]] = {d["key"]: d for d in raw["dimensions"]}
        self._by_id: dict[str, dict[str, Any]] = {d["id"]: d for d in raw["dimensions"]}
        self._layers: dict[str, dict[str, Any]] = {lay["id"]: lay for lay in raw["layers"]}

    # Mapping protocol over the raw JSON --------------------------------------------------------
    def __getitem__(self, item: str) -> Any:
        return self.raw[item]

    def __iter__(self) -> Iterator[str]:
        return iter(self.raw)

    def __len__(self) -> int:
        return len(self.raw)

    def __repr__(self) -> str:
        return (f"Schema(version={self.version!r}, layers={len(self._layers)}, "
                f"dimensions={len(self._by_key)})")

    # Helpers ------------------------------------------------------------------------------------
    @property
    def version(self) -> str | None:
        """``schema_version`` of the coding sheet (``"1.0.0"`` for the frozen v1)."""
        return self.raw.get("schema_version")

    @property
    def keys_in_order(self) -> list[str]:
        """Dimension keys in schema order (A1 ... M7)."""
        return [d["key"] for d in self.raw["dimensions"]]

    @property
    def layers(self) -> dict[str, str]:
        """Layer id to layer name, in schema order (``{"A": "Context assembly", ...}``)."""
        return {lid: lay["name"] for lid, lay in self._layers.items()}

    def dimension(self, key: str) -> dict[str, Any]:
        """One dimension's spec, looked up by key (``"self_verification"``) or id (``"E1"``)."""
        spec = self._by_key.get(key) or self._by_id.get(key)
        if spec is None:
            known = ", ".join(self.keys_in_order)
            raise KeyError(f"unknown dimension {key!r}; known keys: {known}")
        return spec

    def key(self, key_or_id: str) -> str:
        """Normalise a dimension id or key to its key."""
        return self.dimension(key_or_id)["key"]

    def values(self, key: str | None = None) -> Any:  # type: ignore[override]
        """Allowed values of an enum dimension, in schema order.

        Returns an empty list for the non-enum dimensions (``tool_count``, ``stars`` are integers,
        ``first_release_date`` is a date string, ``pinned_version`` free text). Called without a
        key it falls back to the mapping's own ``values()``.
        """
        if key is None:
            return self.raw.values()
        return list(self.dimension(key).get("values") or [])

    def is_multi(self, key: str) -> bool:
        """True when the dimension is multi-valued: its coded value is a list of allowed values."""
        return bool(self.dimension(key).get("multi"))

    def type(self, key: str) -> str:
        """``"enum"``, ``"integer"``, ``"date"`` or ``"string"``."""
        return str(self.dimension(key)["type"])

    def layer_of(self, key: str) -> str:
        """Layer id (``"A"`` ... ``"H"``, ``"M"``) of a dimension."""
        return str(self.dimension(key)["layer"])

    @property
    def table(self) -> pd.DataFrame:
        """One row per dimension: id, key, layer, layer_name, name, type, multi, values."""
        rows = [{
            "dimension_id": d["id"], "dimension_key": d["key"], "layer": d["layer"],
            "layer_name": self._layers.get(d["layer"], {}).get("name", d["layer"]),
            "name": d.get("name"), "type": d["type"], "multi": bool(d.get("multi")),
            "values": list(d.get("values") or []),
        } for d in self.raw["dimensions"]]
        return pd.DataFrame(rows)
