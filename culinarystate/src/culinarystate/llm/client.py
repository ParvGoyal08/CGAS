r"""
K13 — one LLM client for development (Ollama, local, free) and the locked runs
(Claude API — gated by H3; not callable until approved and a key is configured).

Every call is logged to logs/llm/calls.jsonl: model, params, prompt hash, latency,
response hash. Temperature 0 and a fixed seed by default (reproducibility, Part Q2).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from dataclasses import dataclass

import requests

ROOT = pathlib.Path(__file__).resolve().parents[3]
LOG = ROOT / "logs" / "llm" / "calls.jsonl"


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


@dataclass
class OllamaBackend:
    model: str = "qwen2.5:3b"
    url: str = "http://localhost:11434/api/generate"
    temperature: float = 0.0
    seed: int = 20261008
    num_predict: int = 256

    def generate(self, system: str, prompt: str, tag: str = "") -> str:
        t0 = time.time()
        r = requests.post(self.url, json={
            "model": self.model, "system": system, "prompt": prompt, "stream": False,
            "options": {"temperature": self.temperature, "seed": self.seed, "num_predict": self.num_predict}},
            timeout=300)
        r.raise_for_status()
        out = r.json().get("response", "")
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps({"ts": time.time(), "backend": "ollama", "model": self.model, "tag": tag,
                                 "temperature": self.temperature, "seed": self.seed,
                                 "system_sha": _h(system), "prompt_sha": _h(prompt), "response_sha": _h(out),
                                 "latency_s": round(time.time() - t0, 3)}) + "\n")
        return out


class ClaudeBackend:
    """Locked-run backend. Refuses to run without explicit H3 approval (CULINARYSTATE_H3_APPROVED=1)
    and an API key; model and pricing are confirmed at that time."""

    def __init__(self, model: str):
        self.model = model

    def generate(self, system: str, prompt: str, tag: str = "") -> str:
        if os.environ.get("CULINARYSTATE_H3_APPROVED") != "1" or not os.environ.get("ANTHROPIC_API_KEY"):
            raise PermissionError("Claude API runs need H3 approval and a configured key (DEC-005)")
        raise NotImplementedError("wire the Anthropic SDK here after H3 approval")


class TemplateVerbaliser:
    """Deterministic verbaliser: restates the packet's evidence lines and precision policy only.
    Used by the demo and as the B5 claim-guard fallback."""

    def generate(self, system: str, prompt: str, tag: str = "") -> str:
        lines = [ln for ln in prompt.splitlines() if ln.startswith("[EVD-")]
        prec = next((ln.split(":", 1)[1].strip() for ln in prompt.splitlines() if ln.startswith("ALLOWED PRECISION")), "")
        return (f"{prec}. Based on: " + "; ".join(lines[:3])) if lines else "No usable evidence lines in the packet."
