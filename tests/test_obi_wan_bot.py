import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "obi-wan"))

import bot


class Cfg:
    sol_chat_id = 1030157568


class FakeRag:
    def retrieve(self, q, k=5): return [{"source": "x.md", "text": "ctx"}]


def test_is_authorized():
    assert bot.is_authorized(1030157568, 1030157568)
    assert not bot.is_authorized(42, 1030157568)


def test_handle_update_ignores_unauthorized():
    upd = {"message": {"chat": {"id": 42}, "text": "oi"}}
    out = bot.handle_update(upd, Cfg(), FakeRag(), "tok",
                            brain_fn=lambda q, c, ch: "NUNCA", context_fn=lambda t: "ctx")
    assert out is None


def test_handle_update_answers_authorized():
    upd = {"message": {"chat": {"id": 1030157568}, "text": "qual banco do zion?"}}
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
