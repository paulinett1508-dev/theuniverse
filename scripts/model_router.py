"""Model Router — seleciona o melhor modelo disponível por tipo de query.

Estado em state/model-state.json (atualizado pelo model_scout.py).
Fallback garantido: nunca quebra mesmo sem arquivo de estado.
"""
import json
import re
from pathlib import Path

_STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "model-state.json"
_FALLBACK_MODEL = "openai/gpt-oss-120b"

DEFAULT_STATE = {
    "tiers": {
        "fast":     "llama-3.1-8b-instant",
        "balanced": "openai/gpt-oss-120b",
    },
    "models": [],
}

_COMPLEX_KEYWORDS = {
    "explica", "analisa", "compara", "arquitetura", "detalha",
    "descreve", "resume", "relaciona", "investiga", "diagnos",
    "estrutura", "implica", "consequência", "funciona", "fluxo",
}

_FAST_THRESHOLD_WORDS = 12


def classify_query(question: str) -> str:
    """Classifica a query em 'fast' ou 'balanced'."""
    words = question.split()
    q_lower = question.lower()
    if any(kw in q_lower for kw in _COMPLEX_KEYWORDS):
        return "balanced"
    if len(words) >= _FAST_THRESHOLD_WORDS:
        return "balanced"
    return "fast"


def _classify_groq_model(model_id: str) -> str:
    """Infere o tier de um modelo pelo ID."""
    mid = model_id.lower()
    if any(x in mid for x in ("8b", "9b", "3b", "1b", "instant", "small", "mini")):
        return "fast"
    return "balanced"


def _score_model(model: dict) -> float:
    """Pontua um modelo para ranking dentro do mesmo tier."""
    ctx = model.get("context_window", 8192)
    return ctx / 1_000_000  # normalizado; mais contexto = melhor score


def select_model(tier: str, state: dict) -> str:
    """Retorna o model ID mais adequado para o tier dado."""
    tiers = state.get("tiers") or {}
    if tier in tiers:
        return tiers[tier]
    if "balanced" in tiers:
        return tiers["balanced"]
    return _FALLBACK_MODEL


def load_state() -> dict:
    try:
        if _STATE_FILE.exists():
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULT_STATE


def route(question: str, state: dict | None = None) -> str:
    """Retorna o model ID ideal para a pergunta dada."""
    if state is None:
        state = load_state()
    tier = classify_query(question)
    return select_model(tier, state)
