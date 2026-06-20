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


def is_authorized(chat_id, sol_chat_id):
    return chat_id == sol_chat_id


def extract_reply_context(msg: dict) -> str | None:
    """Se a mensagem é reply a uma notificação do bot, retorna o texto original."""
    reply_to = msg.get("reply_to_message") or {}
    text = (reply_to.get("text") or "").strip()
    return text if text else None


def handle_update(update, cfg, rag, tok, brain_fn, context_fn):
    msg = update.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    if not is_authorized(chat_id, cfg.sol_chat_id):
        log.warning("Ignorado chat_id não autorizado: %s", chat_id)
        return None
    question = (msg.get("text") or "").strip()
    if not question:
        return None
    reply_context = extract_reply_context(msg)
    if reply_context:
        log.info("Reply detectado — contexto: %.60s…", reply_context.replace("\n", " "))
    context_str = context_fn(tok)
    chunks = rag.retrieve(question)
    return brain_fn(question, context_str, chunks, reply_context)


def _send(tg_token, chat_id, text):
    httpx.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
               json={"chat_id": chat_id, "text": text}, timeout=30)


def main():
    cfg = Config()
    tok = gh_token()
    rag = Rag.from_paths(KNOWLEDGE_PATHS)
    log.info("Oráculo online. Indexados %d chunks. Long-polling iniciado.", len(rag.chunks))

    _history = []
    _ctx_repo = [None]  # repo ativo na conversa (extraído do reply_context)

    def context_fn(t):
        try:
            return context.gather(t)
        except Exception:
            log.exception("contexto ao vivo falhou")
            return "## Estado atual do universo\n(estado ao vivo indisponível agora)"

    def brain_fn(q, c, ch, reply_context=None):
        if reply_context:
            facts = brain._parse_notification(reply_context)
            if facts.get("repo"):
                _ctx_repo[0] = facts["repo"]
        result = brain.answer(q, c, ch, cfg.groq_api_key, cfg.groq_model,
                              reply_context=reply_context,
                              history=list(_history),
                              ctx_repo=_ctx_repo[0])
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
                try:
                    reply = handle_update(upd, cfg, rag, tok, brain_fn, context_fn)
                except Exception:
                    log.exception("falha ao responder")
                    reply = "Oráculo indisponível, tenta de novo."
                if reply:
                    _send(cfg.telegram_token, cfg.sol_chat_id, reply)
        except Exception:
            log.exception("erro no loop de polling")
            time.sleep(5)


if __name__ == "__main__":
    main()
