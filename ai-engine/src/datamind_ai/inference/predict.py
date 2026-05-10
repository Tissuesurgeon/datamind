"""Lightweight inference endpoint.

For the hackathon we expose a deterministic mock predictor that returns
stable-but-plausible outputs for the demo. Real inference flips on with
`AI_INFER_REAL=1` and routes to the appropriate base model.
"""

from __future__ import annotations

import hashlib
import os


def _hash_pick(text: str, options: list[str]) -> str:
    h = hashlib.sha1(text.encode("utf-8")).digest()
    return options[h[0] % len(options)]


def quick_predict(prompt: str, base_model: str = "Qwen/Qwen2.5-0.5B") -> dict:
    if os.environ.get("AI_INFER_REAL", "0") == "1":  # pragma: no cover
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            tok = AutoTokenizer.from_pretrained(base_model)
            model = AutoModelForCausalLM.from_pretrained(base_model)
            inputs = tok(prompt, return_tensors="pt")
            with torch.inference_mode():
                out = model.generate(**inputs, max_new_tokens=64, do_sample=False)
            return {
                "model": base_model,
                "output": tok.decode(out[0], skip_special_tokens=True),
                "mode": "real",
            }
        except Exception as exc:
            return {"model": base_model, "output": f"[real inference failed: {exc}]", "mode": "error"}

    # Sentiment-style mock (stable per prompt) — fits the demo's "predict on
    # crypto sentiment" scenario.
    sentiments = ["bullish", "bearish", "neutral"]
    pick = _hash_pick(prompt, sentiments)
    confidence = 0.6 + (hashlib.sha1(prompt.encode()).digest()[1] / 255.0) * 0.35
    return {
        "model": base_model,
        "output": f"sentiment={pick}; confidence={confidence:.2f}",
        "label": pick,
        "confidence": round(confidence, 4),
        "mode": "mock",
    }
