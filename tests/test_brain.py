import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "obi-wan"))

import brain


# ── SYSTEM_PROMPT invariants ──────────────────────────────────────────────────

def test_system_prompt_forbids_opening_greetings():
    """Prompt deve proibir explicitamente saudações de abertura."""
    assert "saudações" in brain.SYSTEM_PROMPT or "Olá!" in brain.SYSTEM_PROMPT


def test_system_prompt_forbids_self_introduction():
    """Prompt deve proibir frases tipo 'Estou aqui para ajudar'."""
    assert "para ajudar" in brain.SYSTEM_PROMPT or "auto-apresentação" in brain.SYSTEM_PROMPT


def test_system_prompt_mandates_bullets_for_lists():
    """Prompt deve exigir bullets para listas, não parágrafos."""
    assert "bullets" in brain.SYSTEM_PROMPT and "parágrafos" in brain.SYSTEM_PROMPT


def test_system_prompt_limits_greeting_response():
    """Resposta a saudações simples deve ser 1 linha."""
    assert "saudações simples" in brain.SYSTEM_PROMPT or "olá" in brain.SYSTEM_PROMPT.lower()


def test_system_prompt_forbids_unrequested_status():
    """Prompt deve proibir status não pedido."""
    assert "não pedido" in brain.SYSTEM_PROMPT or "status" in brain.SYSTEM_PROMPT


# ── build_messages ────────────────────────────────────────────────────────────

def test_build_messages_includes_system_prompt():
    msgs = brain.build_messages("oi", "", [])
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == brain.SYSTEM_PROMPT


def test_build_messages_question_in_user_turn():
    msgs = brain.build_messages("quem é a Matrix?", "", [])
    last = msgs[-1]
    assert last["role"] == "user"
    assert "quem é a Matrix?" in last["content"]


def test_build_messages_rag_block_present():
    chunks = [{"source": "planets/nexus.md", "text": "CI verde"}]
    msgs = brain.build_messages("status nexus?", "", chunks)
    user_content = msgs[-1]["content"]
    assert "CI verde" in user_content
    assert "planets/nexus.md" in user_content


def test_build_messages_no_rag_shows_placeholder():
    msgs = brain.build_messages("status?", "", [])
    assert "(nada recuperado)" in msgs[-1]["content"]


def test_build_messages_reply_context_injected():
    reply = "🌍 nexus · main · 14:30\n\nfix: login\n— paulinett1508-dev"
    msgs = brain.build_messages("o que mudou?", "", [], reply_context=reply)
    user_content = msgs[-1]["content"]
    assert "Notificação em contexto" in user_content
    assert "fix: login" in user_content


def test_build_messages_history_injected():
    history = [
        {"role": "user", "content": "anterior"},
        {"role": "assistant", "content": "resposta anterior"},
    ]
    msgs = brain.build_messages("nova pergunta", "", [], history=history)
    assert msgs[1]["role"] == "user"
    assert msgs[2]["role"] == "assistant"
    assert msgs[-1]["content"].endswith("nova pergunta")
