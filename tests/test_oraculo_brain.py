import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "oraculo"))

import brain


def test_build_messages_includes_context_rag_and_question():
    msgs = brain.build_messages("qual banco do zion?", "## Estado\n- zion: 2d",
                                [{"source": "planets/zion.md", "text": "Zion usa PostgreSQL"}])
    assert msgs[0]["role"] == "system"
    user = msgs[1]["content"]
    assert "zion: 2d" in user
    assert "PostgreSQL" in user
    assert "qual banco do zion?" in user


def test_answer_parses_groq_response():
    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": " Resposta do Oráculo "}}]}

    class FakeClient:
        def __init__(self): self.sent = None
        def post(self, url, headers, json, timeout):
            self.sent = {"url": url, "headers": headers, "json": json}
            return FakeResp()

    client = FakeClient()
    out = brain.answer("p", "ctx", [], "gsk_x", "llama-3.3-70b-versatile", client=client)
    assert out == "Resposta do Oráculo"
    assert client.sent["headers"]["Authorization"] == "Bearer gsk_x"
    assert client.sent["json"]["model"] == "llama-3.3-70b-versatile"
