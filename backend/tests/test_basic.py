"""Smoke tests that don't need a running database / Qdrant."""

from app.services.embeddings.chunker import chunk_text
from app.utils.hashing import keccak256_hex, sha256_hex


def test_chunk_text_short() -> None:
    assert chunk_text("hello") == ["hello"]


def test_chunk_text_paragraphs() -> None:
    text = "\n\n".join(["paragraph " + str(i) for i in range(20)])
    chunks = chunk_text(text, max_chars=80)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 100  # tolerant


def test_sha256_stable() -> None:
    a = sha256_hex("hello")
    b = sha256_hex(b"hello")
    assert a == b
    assert len(a) == 64


def test_keccak256_format() -> None:
    h = keccak256_hex("dataset")
    assert h.startswith("0x") and len(h) == 66
