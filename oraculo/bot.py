"""Oráculo do Universo — bot Telegram conversacional (long-polling) na Polaris."""
import re
import sys
import time
import logging
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh import token as gh_token  # noqa: E402

from config import Config
from rag import Rag
import context
import brain

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s — %(message)s", level=logging.INFO)
log = logging.getLogger("oraculo")

KNOWLEDGE_PATHS = ["planets", "docs/ecossistema", "CHANGELOG.md", "CLAUDE.md"]

# Planetas com governança própria — Oráculo avisa antes de entrar
SOVEREIGN_PLANETS = {"the-matrix", "matrix-core"}

_CONFIRM = {"sim", "s", "pode", "entra", "vai", "yes", "y", "ok", "bora", "confirma"}
_DENY    = {"não", "nao", "n", "cancela", "cancel", "voltar", "no", "deixa"}


def is_authorized(chat_id, sol_chat_id):
    return chat_id == sol_chat_id


def extract_reply_context(msg: dict) -> str | None:
    reply_to = msg.get("reply_to_message") or {}
    text = (reply_to.get("text") or "").strip()
    return text if text else None


def load_planet_names() -> list:
    planets_dir = Path(__file__).resolve().parent.parent / "planets"
    return [f.stem for f in planets_dir.glob("*.md") if f.stem != "_index"]


def detect_planet(question: str, planet_names: list) -> str | None:
    q = question.lower()
    for name in planet_names:
        if name.lower() in q:
            return name
        # match parcial: "nexus" encontra "nexus-labsobral"
        parts = name.split("-")
        if any(len(p) > 3 and p in q for p in parts):
            return name
    return None


def orbit_prompt(repo: str) -> str:
    if repo in SOVEREIGN_PLANETS:
        return (f"🌍 <b>{repo}</b> tem governança própria.\n\n"
                f"Adentro como observador externo?")
    return (f"🌍 Identifico relação com <b>{repo}</b>.\n\n"
            f"Entro na órbita para investigar?")


def _send(tg_token, chat_id, text, parse_mode="HTML"):
    httpx.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
               json={"chat_id": chat_id, "text": text,
                     "parse_mode": parse_mode,
                     "disable_web_page_preview": True},
               timeout=30)


def _typing(tg_token, chat_id):
    try:
        httpx.post(f"https://api.telegram.org/bot{tg_token}/sendChatAction",
                   json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except Exception:
        pass


def main():
    cfg = Config()
    tok = gh_token()
    rag = Rag.from_paths(KNOWLEDGE_PATHS)
    planet_names = load_planet_names()
    log.info("Oráculo online. %d chunks · %d planetas conhecidos.", len(rag.chunks), len(planet_names))

    _history    = []
    _ctx_repo   = [None]
    _pending    = [None]  # {"repo": str, "question": str, "context_str": str, "chunks": list}

    def context_fn(t):
        try:
            return context.gather(t)
        except Exception:
            log.exception("contexto ao vivo falhou")
            return "## Estado atual do universo\n(estado ao vivo indisponível agora)"

    def brain_fn(q, c, ch, reply_context=None, orbit_repo=None):
        repo = orbit_repo or _ctx_repo[0]
        if reply_context:
            facts = brain._parse_notification(reply_context)
            if facts.get("repo"):
                _ctx_repo[0] = facts["repo"]
                repo = _ctx_repo[0]
        result = brain.answer(q, c, ch, cfg.groq_api_key, cfg.groq_model,
                              reply_context=reply_context,
                              history=list(_history),
                              ctx_repo=repo)
        _history.append({"role": "user", "content": q})
        _history.append({"role": "assistant", "content": result})
        while len(_history) > 10:
            _history.pop(0)
        return result

    offset = None
    while True:
        try:
            resp = httpx.get(f"https://api.telegram.org/bot{cfg.telegram_token}/getUpdates",
                             params={"offset": offset, "timeout": 30}, timeout=40)
            for upd in resp.json().get("result", []):
                offset = upd["update_id"] + 1
                msg     = upd.get("message") or {}
                chat_id = (msg.get("chat") or {}).get("id")

                if not is_authorized(chat_id, cfg.sol_chat_id):
                    log.warning("Ignorado chat_id não autorizado: %s", chat_id)
                    continue

                question = (msg.get("text") or "").strip()
                if not question:
                    continue

                _typing(cfg.telegram_token, cfg.sol_chat_id)

                try:
                    reply_context = extract_reply_context(msg)
                    if reply_context:
                        log.info("Reply detectado — contexto: %.60s…", reply_context.replace("\n", " "))

                    # ── confirmação de órbita pendente ──────────────────────
                    if _pending[0] and not reply_context:
                        word = question.lower().strip()
                        if word in _CONFIRM:
                            p = _pending[0]
                            _pending[0] = None
                            _ctx_repo[0] = p["repo"]
                            log.info("Órbita confirmada: %s", p["repo"])
                            reply = brain_fn(p["question"], p["context_str"], p["chunks"],
                                             orbit_repo=p["repo"])
                        elif word in _DENY:
                            _pending[0] = None
                            reply = "Entendido — respondendo do vão do universo."
                        else:
                            # nova pergunta enquanto há pendência — cancela e processa normal
                            _pending[0] = None
                            context_str = context_fn(tok)
                            chunks = rag.retrieve(question)
                            reply = brain_fn(question, context_str, chunks, reply_context)
                        _send(cfg.telegram_token, cfg.sol_chat_id, reply)
                        continue

                    # ── reply a notificação → entra na órbita direto ────────
                    if reply_context:
                        context_str = context_fn(tok)
                        chunks = rag.retrieve(question)
                        reply = brain_fn(question, context_str, chunks, reply_context)
                        _send(cfg.telegram_token, cfg.sol_chat_id, reply)
                        continue

                    # ── mensagem solta → detecta planeta e pede confirmação ─
                    detected = detect_planet(question, planet_names)
                    if detected:
                        context_str = context_fn(tok)
                        chunks = rag.retrieve(question)
                        _pending[0] = {"repo": detected, "question": question,
                                       "context_str": context_str, "chunks": chunks}
                        log.info("Órbita proposta: %s", detected)
                        _send(cfg.telegram_token, cfg.sol_chat_id, orbit_prompt(detected))
                        continue

                    # ── pergunta geral sobre o universo ─────────────────────
                    context_str = context_fn(tok)
                    chunks = rag.retrieve(question)
                    reply = brain_fn(question, context_str, chunks)
                    _send(cfg.telegram_token, cfg.sol_chat_id, reply)

                except Exception:
                    log.exception("falha ao responder")
                    _send(cfg.telegram_token, cfg.sol_chat_id, "Oráculo indisponível, tenta de novo.")

        except Exception:
            log.exception("erro no loop de polling")
            time.sleep(5)


if __name__ == "__main__":
    main()
