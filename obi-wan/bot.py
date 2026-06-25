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
log = logging.getLogger("obi-wan")

KNOWLEDGE_PATHS = ["planets", "docs/ecossistema", "CHANGELOG.md", "CLAUDE.md"]
BOT_USERNAME = "guardiao_universo_bot"

# Planetas com governança própria — Oráculo avisa antes de entrar
SOVEREIGN_PLANETS = {"the-matrix", "matrix-core"}

_CONFIRM = {"sim", "s", "pode", "entra", "vai", "yes", "y", "ok", "bora", "confirma"}
_DENY    = {"não", "nao", "n", "cancela", "cancel", "voltar", "no", "deixa"}

STICKERS = {
    "orbit_proposed":  "CAACAgUAAxUAAWo3FT1cf6siBgI6z0vs1NpTOdNiAAIHAAOGQWgf8vF2xj6PSUI8BA",
    "orbit_confirmed": "CAACAgEAAxUAAWo3FTrOHoaS0ToFU3rEghpW8PgaAAJmAgACBBMFAAHn4iwXiWyJJjwE",
    "orbit_denied":    "CAACAgIAAxUAAWo3FTxRJCoLc1h77sy2r3kjy4-IAALYEAAC123oSWmTENRWGDqGPAQ",
    "no_info":         "CAACAgUAAxUAAWo3FT1Xw1MO9lJ6ysf-yZqaZUy1AAIDAAOGQWgfvKagv4ZFaKE8BA",
}


# ── pure helpers ─────────────────────────────────────────────────────────────

def is_authorized(chat_id, allowed):
    if isinstance(allowed, (int, float)):
        return chat_id == int(allowed)
    return chat_id in allowed


def is_group_msg(msg: dict) -> bool:
    return (msg.get("chat") or {}).get("type") in ("group", "supergroup")


def is_mentioned(text: str, bot_username: str = BOT_USERNAME) -> bool:
    return f"@{bot_username}".lower() in text.lower()


def extract_mention(text: str, bot_username: str = BOT_USERNAME) -> str:
    return re.sub(rf'@{re.escape(bot_username)}\s*', '', text, flags=re.IGNORECASE).strip()


def should_respond_in_group(msg: dict, bot_username: str = BOT_USERNAME) -> bool:
    text = (msg.get("text") or "").strip()
    if is_mentioned(text, bot_username):
        return True
    reply_from = ((msg.get("reply_to_message") or {}).get("from") or {})
    return reply_from.get("username") == bot_username


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


# ── I/O helpers ──────────────────────────────────────────────────────────────

def _send(tg_token, chat_id, text, parse_mode="HTML", thread_id=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode,
              "disable_web_page_preview": True}
    if thread_id:
        params["message_thread_id"] = thread_id
    httpx.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
               json=params, timeout=30)


def _typing(tg_token, chat_id, thread_id=None):
    try:
        params = {"chat_id": chat_id, "action": "typing"}
        if thread_id:
            params["message_thread_id"] = thread_id
        httpx.post(f"https://api.telegram.org/bot{tg_token}/sendChatAction",
                   json=params, timeout=5)
    except Exception:
        pass


def _send_sticker(tg_token, chat_id, key: str, thread_id=None):
    file_id = STICKERS.get(key)
    if not file_id:
        return
    try:
        params = {"chat_id": chat_id, "sticker": file_id}
        if thread_id:
            params["message_thread_id"] = thread_id
        httpx.post(f"https://api.telegram.org/bot{tg_token}/sendSticker",
                   json=params, timeout=10)
    except Exception:
        pass


# ── core logic (testable, no I/O) ────────────────────────────────────────────

def handle_update(upd, cfg, rag, tg_token, brain_fn, context_fn,
                  state=None, bot_username=BOT_USERNAME):
    """
    Process one Telegram update. Returns reply text or None.
    Stickers and side effects remain in main(); this is pure Q&A logic.
    state: optional mutable dict with keys 'history', 'ctx_repo', 'pending'
    """
    if state is None:
        state = {"history": [], "ctx_repo": None, "pending": None}

    msg      = upd.get("message") or {}
    chat_id  = (msg.get("chat") or {}).get("id")
    if not chat_id:
        return None

    group     = is_group_msg(msg)
    thread_id = msg.get("message_thread_id") if group else None  # noqa: F841

    # Build allowed set from cfg
    allowed = {cfg.sol_chat_id}
    gid = getattr(cfg, "group_chat_id", None)
    if gid:
        allowed.add(gid)
    if not is_authorized(chat_id, allowed):
        log.warning("Ignorado chat_id não autorizado: %s", chat_id)
        return None

    # Group: only respond to @mentions or replies-to-bot
    if group and not should_respond_in_group(msg, bot_username):
        return None

    question = (msg.get("text") or "").strip()
    if not question:
        return None

    if group:
        question = extract_mention(question, bot_username)
    if not question:
        return None

    reply_context = extract_reply_context(msg)

    # Pending orbit confirmation (DM only — groups skip this flow)
    if state["pending"] and not group and not reply_context:
        word = question.lower().strip()
        if word in _CONFIRM:
            p = state["pending"]
            state["pending"] = None
            state["ctx_repo"] = p["repo"]
            return brain_fn(p["question"], p["context_str"], p["chunks"])
        if word in _DENY:
            state["pending"] = None
            return "Entendido — respondendo do vão do universo."
        # New question while pending — reset and fall through
        state["pending"] = None

    # Reply to notification → entra na órbita
    if reply_context:
        if not group:
            facts = brain._parse_notification(reply_context)
            if facts.get("repo"):
                state["ctx_repo"] = facts["repo"]
        context_str = context_fn(None)
        effective_q = question if len(question) > 2 else f"status de {reply_context[:30]}"
        chunks = rag.retrieve(effective_q)
        return brain_fn(effective_q, context_str, chunks)

    # Planet detection — orbit proposal only for DMs (groups respond directly)
    detected = detect_planet(question, load_planet_names())
    if detected and not group:
        context_str = context_fn(None)
        chunks = rag.retrieve(question)
        state["pending"] = {"repo": detected, "question": question,
                            "context_str": context_str, "chunks": chunks}
        return None  # caller sends sticker + orbit_prompt

    # General question
    context_str = context_fn(None)
    chunks = rag.retrieve(question)
    return brain_fn(question, context_str, chunks)


# ── main loop ────────────────────────────────────────────────────────────────

def main():
    cfg = Config()
    tok = gh_token()
    rag = Rag.from_paths(KNOWLEDGE_PATHS)
    planet_names = load_planet_names()
    log.info("Oráculo online. %d chunks · %d planetas conhecidos.", len(rag.chunks), len(planet_names))

    state = {"history": [], "ctx_repo": None, "pending": None}

    def context_fn(t):
        try:
            return context.gather(tok)
        except Exception:
            log.exception("contexto ao vivo falhou")
            return "## Estado atual do universo\n(estado ao vivo indisponível agora)"

    def brain_fn(q, c, ch, reply_context=None, orbit_repo=None):
        repo = orbit_repo or state["ctx_repo"]
        if reply_context:
            facts = brain._parse_notification(reply_context)
            if facts.get("repo"):
                state["ctx_repo"] = facts["repo"]
                repo = state["ctx_repo"]
        result = brain.answer(q, c, ch, cfg.groq_api_key, cfg.groq_model,
                              reply_context=reply_context,
                              history=list(state["history"]),
                              ctx_repo=repo)
        state["history"].append({"role": "user", "content": q})
        state["history"].append({"role": "assistant", "content": result})
        while len(state["history"]) > 10:
            state["history"].pop(0)
        return result

    offset = None
    while True:
        try:
            resp = httpx.get(f"https://api.telegram.org/bot{cfg.telegram_token}/getUpdates",
                             params={"offset": offset, "timeout": 30}, timeout=40)
            for upd in resp.json().get("result", []):
                offset = upd["update_id"] + 1
                msg      = upd.get("message") or {}
                chat_id  = (msg.get("chat") or {}).get("id")
                group    = is_group_msg(msg)
                thread_id = msg.get("message_thread_id") if group else None

                _typing(cfg.telegram_token, chat_id, thread_id)

                prev_pending = state["pending"]
                reply = handle_update(upd, cfg, rag, cfg.telegram_token, brain_fn, context_fn,
                                      state=state, bot_username=BOT_USERNAME)

                if reply:
                    _send(cfg.telegram_token, chat_id, reply, thread_id=thread_id)
                elif state["pending"] and not prev_pending:
                    # Orbit proposed — send sticker + prompt
                    p = state["pending"]
                    _send_sticker(cfg.telegram_token, chat_id, "orbit_proposed", thread_id)
                    _send(cfg.telegram_token, chat_id, orbit_prompt(p["repo"]), thread_id=thread_id)
                elif reply is None and not state["pending"] and not group:
                    pass  # denied orbit or empty — sticker already handled elsewhere

        except Exception:
            log.exception("erro no loop de polling")
            time.sleep(5)


if __name__ == "__main__":
    main()
