"""Dataset loaders that return a uniform `LoadedDataset` envelope.

We use Polars where possible (faster + memory-friendly), with a Pandas fallback
for esoteric formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LoadedDataset:
    rows: int
    columns: int
    schema: list[str] = field(default_factory=list)
    sample: list[dict[str, Any]] = field(default_factory=list)
    text_blob: str = ""
    column_data: dict[str, list[Any]] = field(default_factory=dict)
    fmt: str = "txt"


def _load_csv(path: Path) -> LoadedDataset:
    try:
        import polars as pl

        df = pl.read_csv(path, ignore_errors=True, infer_schema_length=200, n_rows=20_000)
        rows, cols = df.shape
        schema = df.columns
        sample = df.head(5).to_dicts()
        col_data = {c: df.get_column(c).to_list()[:200] for c in schema}
        text_blob = "\n".join(", ".join(f"{k}={v}" for k, v in r.items()) for r in df.head(40).to_dicts())
        return LoadedDataset(
            rows=rows,
            columns=cols,
            schema=list(schema),
            sample=sample,
            text_blob=text_blob,
            column_data=col_data,
            fmt="csv",
        )
    except Exception:
        # Pandas fallback
        import pandas as pd

        df = pd.read_csv(path, on_bad_lines="skip", nrows=20_000)
        rows, cols = df.shape
        sample = df.head(5).to_dict(orient="records")
        text_blob = df.head(40).to_string()
        col_data = {c: df[c].head(200).tolist() for c in df.columns}
        return LoadedDataset(
            rows=int(rows),
            columns=int(cols),
            schema=list(df.columns),
            sample=sample,
            text_blob=text_blob,
            column_data=col_data,
            fmt="csv",
        )


def _load_json(path: Path) -> LoadedDataset:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _load_text(path)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        rows = len(data)
        schema = sorted({k for r in data[:200] for k in r.keys()})
        sample = data[:5]
        text_blob = "\n".join(json.dumps(r)[:600] for r in data[:40])
        col_data = {k: [r.get(k) for r in data[:200]] for k in schema}
        return LoadedDataset(
            rows=rows,
            columns=len(schema),
            schema=schema,
            sample=sample,
            text_blob=text_blob,
            column_data=col_data,
            fmt="json",
        )
    return LoadedDataset(rows=1, columns=1, sample=[{"value": data}], text_blob=text[:50_000], fmt="json")


def _load_jsonl(path: Path) -> LoadedDataset:
    rows: list[dict] = []
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except json.JSONDecodeError:
                continue
            if len(rows) >= 20_000:
                break
    if not rows:
        return _load_text(path)
    schema = sorted({k for r in rows[:200] for k in r.keys()})
    sample = rows[:5]
    text_blob = "\n".join(json.dumps(r)[:600] for r in rows[:40])
    col_data = {k: [r.get(k) for r in rows[:200]] for k in schema}
    return LoadedDataset(
        rows=len(rows),
        columns=len(schema),
        schema=schema,
        sample=sample,
        text_blob=text_blob,
        column_data=col_data,
        fmt="jsonl",
    )


def _load_text(path: Path) -> LoadedDataset:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in txt.splitlines() if l.strip()]
    return LoadedDataset(
        rows=len(lines),
        columns=1,
        schema=["text"],
        sample=[{"text": l} for l in lines[:5]],
        text_blob=txt[:50_000],
        column_data={"text": lines[:200]},
        fmt="txt",
    )


def _load_pdf(path: Path) -> LoadedDataset:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n\n".join(pages)
        return LoadedDataset(
            rows=len(pages),
            columns=1,
            schema=["page_text"],
            sample=[{"page": i + 1, "text": p[:300]} for i, p in enumerate(pages[:5])],
            text_blob=text[:50_000],
            column_data={"page_text": pages[:200]},
            fmt="pdf",
        )
    except Exception:
        return LoadedDataset(rows=0, columns=0, fmt="pdf", text_blob=f"Unparseable PDF: {path.name}")


def load_dataset_for_analysis(path: Path | str, fmt: str | None = None) -> LoadedDataset:
    p = Path(path)
    fmt = (fmt or p.suffix.lower().lstrip(".") or "txt").lower()
    if fmt == "csv" or fmt == "tsv":
        return _load_csv(p)
    if fmt == "jsonl":
        return _load_jsonl(p)
    if fmt == "json":
        return _load_json(p)
    if fmt == "pdf":
        return _load_pdf(p)
    return _load_text(p)
