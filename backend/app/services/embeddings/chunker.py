"""Lightweight chunker — used by ingest pipeline to feed Qdrant.

For CSVs and tabular files we serialize each row into a `key=value, …` line.
For text/JSON we paragraph- or window-split.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

DEFAULT_CHARS = 600


def chunk_text(text: str, max_chars: int = DEFAULT_CHARS) -> list[str]:
    if not text:
        return []
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = (buf + "\n\n" + p) if buf else p
        else:
            if buf:
                out.append(buf)
            if len(p) > max_chars:
                # Hard window-split very long paragraphs.
                for i in range(0, len(p), max_chars):
                    out.append(p[i : i + max_chars])
                buf = ""
            else:
                buf = p
    if buf:
        out.append(buf)
    return out


def chunk_csv(path: Path, max_rows_per_chunk: int = 8) -> list[str]:
    out: list[str] = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return []
        rows: list[str] = []
        for row in reader:
            kv = ", ".join(
                f"{h}={(v or '').strip()[:80]}"
                for h, v in zip(header, row)
                if (v or "").strip()
            )
            if kv:
                rows.append(kv)
            if len(rows) >= max_rows_per_chunk:
                out.append("\n".join(rows))
                rows = []
        if rows:
            out.append("\n".join(rows))
    return out


def chunk_jsonl(path: Path, max_rows_per_chunk: int = 8) -> list[str]:
    out: list[str] = []
    rows: list[str] = []
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(", ".join(f"{k}={str(v)[:80]}" for k, v in obj.items()))
                else:
                    rows.append(str(obj)[:600])
            except json.JSONDecodeError:
                rows.append(line[:600])
            if len(rows) >= max_rows_per_chunk:
                out.append("\n".join(rows))
                rows = []
    if rows:
        out.append("\n".join(rows))
    return out


def chunk_file(path: Path, fmt: str | None = None) -> list[str]:
    fmt = (fmt or path.suffix.lower().lstrip(".")).lower()
    if fmt == "csv":
        return chunk_csv(path)
    if fmt == "jsonl":
        return chunk_jsonl(path)
    if fmt == "json":
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return chunk_text(path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(data, list):
            text = "\n\n".join(json.dumps(x)[:1500] for x in data[:200])
            return chunk_text(text)
        return chunk_text(json.dumps(data)[:50_000])
    if fmt == "pdf":
        # Without a PDF dep, treat as bytes summary.
        return chunk_text(f"PDF document: {path.name} ({path.stat().st_size} bytes)")
    return chunk_text(path.read_text(encoding="utf-8", errors="ignore"))
