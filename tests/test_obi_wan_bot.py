import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "obi-wan"))

import bot


class Cfg:
    sol_chat_id = 1030157568
    group_chat_id = None


class CfgWithGroup:
    sol_chat_id = 1030157568
    group_chat_id = -1004472865546


class FakeRag:
    def retrieve(self, q, k=5): return [{"source": "x.md", "text": "ctx"}]


# ── is_authorized ────────────────────────────────────────────────────────────

def test_is_authorized():
    assert bot.is_authorized(1030157568, 1030157568)
    assert not bot.is_authorized(42, 1030157568)


def test_is_authorized_set():
    assert bot.is_authorized(-1004472865546, {1030157568, -1004472865546})
    assert not bot.is_authorized(99, {1030157568, -1004472865546})


# ── is_group_msg ─────────────────────────────────────────────────────────────

def test_is_group_msg_supergroup():
    msg = {"chat": {"id": -1004472865546, "type": "supergroup"}}
    assert bot.is_group_msg(msg)


def test_is_group_msg_group():
    msg = {"chat": {"id": -100, "type": "group"}}
    assert bot.is_group_msg(msg)


def test_is_group_msg_private():
    msg = {"chat": {"id": 1030157568, "type": "private"}}
    assert not bot.is_group_msg(msg)


# ── extract_mention ───────────────────────────────────────────────────────────

def test_extract_mention_at_start():
    result = bot.extract_mention("@guardiao_universo_bot quem é a Matrix?")
    assert result == "quem é a Matrix?"


def test_extract_mention_mid_text():
    result = bot.extract_mention("quem é @guardiao_universo_bot a Matrix?")
    assert "guardiao_universo_bot" not in result


def test_extract_mention_no_mention():
    result = bot.extract_mention("quem é a Matrix?")
    assert result == "quem é a Matrix?"


def test_extract_mention_only_mention():
    result = bot.extract_mention("@guardiao_universo_bot")
    assert result == ""


# ── is_mentioned ─────────────────────────────────────────────────────────────

def test_is_mentioned_true():
    assert bot.is_mentioned("@guardiao_universo_bot status?")


def test_is_mentioned_false():
    assert not bot.is_mentioned("status do universo?")


def test_is_mentioned_case_insensitive():
    assert bot.is_mentioned("@Guardiao_Universo_Bot oi")


# ── should_respond_in_group ───────────────────────────────────────────────────

def test_should_respond_mention():
    msg = {"text": "@guardiao_universo_bot quem é a Matrix?"}
    assert bot.should_respond_in_group(msg)


def test_should_respond_reply_to_bot():
    msg = {
        "text": "explica mais",
        "reply_to_message": {"from": {"username": "guardiao_universo_bot"}},
    }
    assert bot.should_respond_in_group(msg)


def test_should_not_respond_plain_group():
    msg = {"text": "oi galera"}
    assert not bot.should_respond_in_group(msg)


# ── handle_update ─────────────────────────────────────────────────────────────

def test_handle_update_ignores_unauthorized():
    upd = {"message": {"chat": {"id": 42, "type": "private"}, "text": "oi"}}
    out = bot.handle_update(upd, Cfg(), FakeRag(), "tok",
                            brain_fn=lambda q, c, ch: "NUNCA",
                            context_fn=lambda t: "ctx")
    assert out is None


def test_handle_update_answers_authorized():
    upd = {"message": {"chat": {"id": 1030157568, "type": "private"},
                        "text": "qual banco do zion?"}}
    captured = {}

    def brain_fn(q, c, ch):
        captured["q"], captured["c"], captured["ch"] = q, c, ch
        return "Zion usa PostgreSQL"

    out = bot.handle_update(upd, Cfg(), FakeRag(), "tok",
                            brain_fn=brain_fn, context_fn=lambda t: "## Estado vivo")
    assert out == "Zion usa PostgreSQL"
    assert captured["q"] == "qual banco do zion?"
    assert captured["c"] == "## Estado vivo"
    assert captured["ch"] == [{"source": "x.md", "text": "ctx"}]


def test_handle_update_group_responds_to_plain_msg():
    # privacy mode off — bot responde a mensagens sem @mention no grupo autorizado
    upd = {"message": {"chat": {"id": -1004472865546, "type": "supergroup"},
                        "text": "olá universo"}}
    out = bot.handle_update(upd, CfgWithGroup(), FakeRag(), "tok",
                            brain_fn=lambda q, c, ch: "olá TheGod",
                            context_fn=lambda t: "ctx")
    assert out == "olá TheGod"


def test_handle_update_group_responds_to_mention():
    upd = {"message": {"chat": {"id": -1004472865546, "type": "supergroup"},
                        "text": "@guardiao_universo_bot quem é a Matrix?",
                        "message_thread_id": 4}}
    out = bot.handle_update(upd, CfgWithGroup(), FakeRag(), "tok",
                            brain_fn=lambda q, c, ch: "Matrix é o ecossistema Sobral",
                            context_fn=lambda t: "ctx")
    assert out == "Matrix é o ecossistema Sobral"


def test_handle_update_group_strips_mention():
    upd = {"message": {"chat": {"id": -1004472865546, "type": "supergroup"},
                        "text": "@guardiao_universo_bot quem é a Matrix?"}}
    captured = {}

    def brain_fn(q, c, ch):
        captured["q"] = q
        return "resposta"

    bot.handle_update(upd, CfgWithGroup(), FakeRag(), "tok",
                      brain_fn=brain_fn, context_fn=lambda t: "ctx")
    assert "@guardiao_universo_bot" not in captured.get("q", "")
    assert "Matrix" in captured.get("q", "")


# ── handle_reaction ────────────────────────────────────────────────────────────

def _reaction_upd(message_id=42, user_id=1030157568, emojis=None):
    return {"message_reaction": {
        "chat": {"id": -1004472865546},
        "message_id": message_id,
        "user": {"id": user_id},
        "new_reaction": [{"type": "emoji", "emoji": e} for e in (emojis or ["✅"])],
        "old_reaction": [],
    }}


def test_handle_reaction_closes_issue():
    ack = {"42": "https://github.com/paulinett1508-dev/nexus/issues/7"}
    closed = []

    result = bot.handle_reaction(
        _reaction_upd(),
        CfgWithGroup(),
        gh_token="tok",
        ack_load_fn=lambda: ack,
        close_fn=lambda url: closed.append(url),
    )

    assert closed == ["https://github.com/paulinett1508-dev/nexus/issues/7"]
    assert result is not None and len(result) > 0


def test_handle_reaction_ignores_unknown_message():
    result = bot.handle_reaction(
        _reaction_upd(message_id=999),
        CfgWithGroup(),
        gh_token="tok",
        ack_load_fn=lambda: {"42": "https://gh/issues/7"},
        close_fn=lambda url: None,
    )
    assert result is None


def test_handle_reaction_ignores_non_checkmark():
    result = bot.handle_reaction(
        _reaction_upd(emojis=["👍"]),
        CfgWithGroup(),
        gh_token="tok",
        ack_load_fn=lambda: {"42": "https://gh/issues/7"},
        close_fn=lambda url: None,
    )
    assert result is None


def test_handle_reaction_ignores_unauthorized_user():
    result = bot.handle_reaction(
        _reaction_upd(user_id=9999),
        CfgWithGroup(),
        gh_token="tok",
        ack_load_fn=lambda: {"42": "https://gh/issues/7"},
        close_fn=lambda url: None,
    )
    assert result is None


def test_handle_reaction_returns_none_if_no_reaction_key():
    result = bot.handle_reaction(
        {"message": {"text": "oi"}},
        CfgWithGroup(),
        gh_token="tok",
        ack_load_fn=lambda: {},
        close_fn=lambda url: None,
    )
    assert result is None
