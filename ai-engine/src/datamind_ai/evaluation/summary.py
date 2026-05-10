"""Cheap, deterministic dataset summary.

We intentionally avoid loading a generation model — the demo doesn't need a
multi-billion-parameter summarizer for a 200-word blurb. We compose a clear,
factual summary from the analyzer's structured fields.
"""

from __future__ import annotations


def generate_summary(
    *,
    title: str,
    rows: int,
    columns: int,
    fmt: str,
    quality_score: float,
    duplicate_ratio: float,
    missing_ratio: float,
    semantic_tags: list[str],
    topics: list[dict],
) -> str:
    grade = "A" if quality_score >= 0.85 else "B" if quality_score >= 0.65 else "C"
    tag_phrase = ", ".join(semantic_tags[:5]) if semantic_tags else "general"
    topic_phrase = ", ".join(t.get("label", "") for t in topics[:3]) or "no dominant themes"

    return (
        f"{title or 'Dataset'} — {rows:,} rows × {columns} columns ({fmt}). "
        f"Quality grade {grade} (score {quality_score:.2f}). "
        f"Duplicate ratio {duplicate_ratio:.1%}, missingness {missing_ratio:.1%}. "
        f"Semantic profile: {tag_phrase}. "
        f"Top topics: {topic_phrase}."
    )
