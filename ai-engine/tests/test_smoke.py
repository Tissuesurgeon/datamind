"""Smoke tests that exercise the deterministic embedding fallback."""

from datamind_ai.embeddings import embed_one, get_dim


def test_embed_one_dimension() -> None:
    vec = embed_one("hello world")
    assert isinstance(vec, list)
    assert len(vec) == get_dim()
    # L2 normalized — magnitude near 1.
    mag = sum(v * v for v in vec) ** 0.5
    assert 0.95 < mag < 1.05


def test_embed_one_deterministic() -> None:
    a = embed_one("crypto sentiment trading")
    b = embed_one("crypto sentiment trading")
    assert a[:5] == b[:5]
