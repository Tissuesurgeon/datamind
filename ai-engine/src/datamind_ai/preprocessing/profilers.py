"""Per-column profiling: completeness, uniqueness, simple type detection."""

from __future__ import annotations

from typing import Any


def _classify(values: list[Any]) -> str:
    if not values:
        return "empty"
    sample = [v for v in values if v not in (None, "", "null")]
    if not sample:
        return "missing"
    n_int = sum(1 for v in sample if isinstance(v, bool) is False and isinstance(v, int))
    n_float = sum(1 for v in sample if isinstance(v, float))
    n_bool = sum(1 for v in sample if isinstance(v, bool))
    n_str = sum(1 for v in sample if isinstance(v, str))
    if n_bool == len(sample):
        return "boolean"
    if n_int + n_float == len(sample):
        return "numeric"
    if n_str == len(sample):
        # Try to detect date-ish values
        if all(("-" in str(v) or "/" in str(v)) and any(c.isdigit() for c in str(v)) for v in sample[:20]):
            return "datetime"
        return "string"
    return "mixed"


def profile_columns(column_data: dict[str, list[Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for col, values in column_data.items():
        n = len(values)
        non_null = [v for v in values if v not in (None, "", "null")]
        unique = len(set(map(str, non_null)))
        out[col] = {
            "count": n,
            "missing_ratio": round(1 - len(non_null) / max(n, 1), 4),
            "unique_ratio": round(unique / max(len(non_null), 1), 4),
            "type": _classify(values),
        }
    return out
