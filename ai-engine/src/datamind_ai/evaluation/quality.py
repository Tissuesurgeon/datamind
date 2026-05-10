"""Dataset quality scoring.

A weighted blend of:
    completeness        — 1 - mean(missing_ratio)
    uniqueness          — 1 - duplicate_ratio  (low=better)
    schema_consistency  — share of columns with a clean dtype
    text_density        — text-bearing rows ratio (helpful for AI workflows)
"""

from __future__ import annotations

from typing import Any


def compute_quality(
    *,
    column_profile: dict[str, dict[str, Any]],
    rows: int,
    columns: int,
    duplicate_ratio: float,
    text_density: float,
) -> tuple[float, dict[str, float]]:
    if not column_profile:
        # Pure-text payload: completeness from non-empty ratio, uniqueness from text_density.
        completeness = max(0.0, min(1.0, text_density))
        uniqueness = max(0.0, 1.0 - duplicate_ratio)
        schema_consistency = 0.7
    else:
        completeness = 1.0 - (
            sum(v.get("missing_ratio", 0.0) for v in column_profile.values())
            / max(len(column_profile), 1)
        )
        clean = sum(1 for v in column_profile.values() if v.get("type") not in ("mixed", "missing", "empty"))
        schema_consistency = clean / max(len(column_profile), 1)
        uniqueness = max(0.0, 1.0 - duplicate_ratio)

    score = (
        0.32 * completeness
        + 0.28 * uniqueness
        + 0.22 * schema_consistency
        + 0.18 * max(0.0, min(1.0, text_density))
    )
    score = round(max(0.0, min(1.0, score)), 4)
    metrics = {
        "completeness": round(completeness, 4),
        "uniqueness": round(uniqueness, 4),
        "schema_consistency": round(schema_consistency, 4),
        "text_density": round(text_density, 4),
    }
    return score, metrics


def grade_from_score(score: float) -> str:
    if score >= 0.85:
        return "A"
    if score >= 0.65:
        return "B"
    return "C"
