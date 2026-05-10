"""Full dataset analyze pipeline: load → profile → quality → tags → summary."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from datamind_ai.evaluation.quality import compute_quality, grade_from_score
from datamind_ai.evaluation.summary import generate_summary
from datamind_ai.evaluation.tags import extract_semantic_tags, extract_topics
from datamind_ai.preprocessing import load_dataset_for_analysis, profile_columns


@dataclass
class AnalyzeResult:
    summary: str
    semantic_tags: list[str]
    topics: list[dict]
    quality_metrics: dict[str, Any]
    duplicate_ratio: float
    missing_ratio: float
    column_profile: dict[str, Any]
    sample_rows: list[dict[str, Any]]
    rows: int
    columns: int
    quality_score: float
    ai_readiness: float
    quality_grade: str

    def to_dict(self) -> dict:
        return asdict(self)


def _duplicate_ratio(text_blob: str, lines_to_compare: int = 200) -> float:
    if not text_blob:
        return 0.0
    lines = [l.strip() for l in text_blob.splitlines() if l.strip()][:lines_to_compare]
    if not lines:
        return 0.0
    unique = len(set(lines))
    return round(1.0 - unique / len(lines), 4)


def _missing_ratio(column_profile: dict) -> float:
    if not column_profile:
        return 0.0
    return round(
        sum(v.get("missing_ratio", 0.0) for v in column_profile.values()) / max(len(column_profile), 1),
        4,
    )


def _text_density(text_blob: str) -> float:
    if not text_blob:
        return 0.0
    nonblank = sum(1 for c in text_blob if not c.isspace())
    return min(1.0, nonblank / max(len(text_blob), 1))


def analyze_dataset(path: Path | str, fmt: str | None = None, title: str = "") -> AnalyzeResult:
    loaded = load_dataset_for_analysis(path, fmt)
    column_profile = profile_columns(loaded.column_data) if loaded.column_data else {}

    duplicate_ratio = _duplicate_ratio(loaded.text_blob)
    missing_ratio = _missing_ratio(column_profile)
    text_density = _text_density(loaded.text_blob)

    quality_score, quality_metrics = compute_quality(
        column_profile=column_profile,
        rows=loaded.rows,
        columns=loaded.columns,
        duplicate_ratio=duplicate_ratio,
        text_density=text_density,
    )
    quality_grade = grade_from_score(quality_score)
    ai_readiness = round(min(1.0, quality_score * 0.7 + text_density * 0.3), 4)

    semantic_tags = extract_semantic_tags(loaded.text_blob, top_k=7)
    topics = extract_topics(loaded.text_blob, top_k=5)

    summary = generate_summary(
        title=title,
        rows=loaded.rows,
        columns=loaded.columns,
        fmt=loaded.fmt,
        quality_score=quality_score,
        duplicate_ratio=duplicate_ratio,
        missing_ratio=missing_ratio,
        semantic_tags=semantic_tags,
        topics=topics,
    )

    return AnalyzeResult(
        summary=summary,
        semantic_tags=semantic_tags,
        topics=topics,
        quality_metrics=quality_metrics,
        duplicate_ratio=duplicate_ratio,
        missing_ratio=missing_ratio,
        column_profile=column_profile,
        sample_rows=loaded.sample,
        rows=loaded.rows,
        columns=loaded.columns,
        quality_score=quality_score,
        ai_readiness=ai_readiness,
        quality_grade=quality_grade,
    )
