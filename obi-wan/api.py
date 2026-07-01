"""API REST do Obi-Wan — endpoint /ask para comunicação M2M planeta ↔ Observatório."""
import hmac
import os
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

import rag as rag_mod
import context as ctx_mod
import brain

# --- Config (lida do EnvironmentFile do systemd: /opt/obi-wan/.env) ---
_GROQ_API_KEY = os.environ["GROQ_API_KEY"]
_GROQ_MODEL   = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
_GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
_API_TOKEN    = os.environ["API_TOKEN"]   # Bearer token global compartilhado pelos planetas

# --- RAG carregado uma vez no startup ---
_REPO_ROOT = Path(__file__).resolve().parent.parent
_rag = rag_mod.Rag.from_paths([
    _REPO_ROOT / "planets",
    _REPO_ROOT / "docs",
    _REPO_ROOT / "CHANGELOG.md",
    _REPO_ROOT / "CLAUDE.md",
])

# --- Rate limit: 10 req/min por planeta ---
_rate: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT  = 10
_RATE_WINDOW = 60.0

app = FastAPI(title="Obi-Wan /ask", docs_url=None, redoc_url=None)


class AskRequest(BaseModel):
    planet: str
    question: str
    context: dict | None = None


def _auth(request: Request) -> None:
    header = request.headers.get("Authorization", "")
    supplied = header[7:] if header.startswith("Bearer ") else ""
    if not hmac.compare_digest(supplied, _API_TOKEN):
        raise HTTPException(status_code=401)


def _rate_check(ip: str) -> None:
    now = time.monotonic()
    hits = [t for t in _rate[ip] if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    hits.append(now)
    if hits:
        _rate[ip] = hits
    else:
        _rate.pop(ip, None)


@app.post("/ask")
def ask(body: AskRequest, request: Request):
    _auth(request)
    _rate_check(request.client.host)

    question = body.question
    if body.context:
        extra = ", ".join(f"{k}={v}" for k, v in body.context.items())
        question = f"{question} [contexto: {extra}]"

    chunks      = _rag.retrieve(question)
    context_str = ctx_mod.gather(_GITHUB_TOKEN)
    answer      = brain.answer(question, context_str, chunks, _GROQ_API_KEY, _GROQ_MODEL)
    sources     = list(dict.fromkeys(c["source"] for c in chunks))

    return {"planet": body.planet, "answer": answer, "sources": sources}
