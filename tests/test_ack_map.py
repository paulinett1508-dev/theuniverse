import sys
import json
import base64
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import ack_map


def _fake_file(entries: dict, sha="abc123"):
    content = json.dumps({"entries": entries}, indent=2).encode()
    data = json.dumps({
        "content": base64.b64encode(content).decode() + "\n",
        "sha": sha,
    }).encode()

    class FakeResp:
        status = 200
        def read(self): return data
        def __enter__(self): return self
        def __exit__(self, *a): pass

    return FakeResp()


# ── load ──────────────────────────────────────────────────────────────────────

def test_load_returns_entries(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **kw: _fake_file({"99": "https://gh/issues/1"}))
    result = ack_map.load("tok")
    assert result == {"99": "https://gh/issues/1"}


def test_load_returns_empty_on_error(monkeypatch):
    def raise_always(*a, **kw): raise OSError("404")
    monkeypatch.setattr(urllib.request, "urlopen", raise_always)
    assert ack_map.load("tok") == {}


# ── save_entry ────────────────────────────────────────────────────────────────

def test_save_entry_includes_new_entry(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=30):
        calls.append((req.get_method(), req.data))
        # First call is GET (read), second is PUT (write)
        if req.get_method() == "GET" or (hasattr(req, "full_url") and "PUT" not in str(req)):
            return _fake_file({"1": "https://gh/issues/1"})
        class W:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return W()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    ack_map.save_entry(999, "https://gh/issues/5", "tok")

    put_call = next((c for c in calls if c[0] == "PUT"), None)
    assert put_call is not None
    body = json.loads(put_call[1])
    decoded = json.loads(base64.b64decode(body["content"]).decode())
    assert decoded["entries"]["999"] == "https://gh/issues/5"
    assert decoded["entries"]["1"] == "https://gh/issues/1"  # preserva existente
    assert body["sha"] == "abc123"


def test_save_entry_uses_put_method(monkeypatch):
    methods = []

    def fake_urlopen(req, timeout=30):
        methods.append(req.get_method())
        class R:
            def read(self): return json.dumps({"content": base64.b64encode(b'{"entries":{}}').decode(), "sha": "x"}).encode()
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return R()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    ack_map.save_entry(1, "url", "tok")
    assert "PUT" in methods


# ── close_issue ───────────────────────────────────────────────────────────────

def test_close_issue_patches_correct_url(monkeypatch):
    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data)
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = ack_map.close_issue(
        "https://github.com/paulinett1508-dev/nexus/issues/7", "tok"
    )

    assert result is True
    assert "nexus/issues/7" in captured["url"]
    assert captured["method"] == "PATCH"
    assert captured["body"]["state"] == "closed"


def test_close_issue_returns_false_for_invalid_url(monkeypatch):
    assert ack_map.close_issue("not-a-gh-url", "tok") is False


def test_close_issue_propagates_http_error(monkeypatch):
    def raise_always(*a, **kw): raise OSError("500")
    monkeypatch.setattr(urllib.request, "urlopen", raise_always)
    try:
        ack_map.close_issue("https://github.com/o/r/issues/1", "tok")
        assert False, "deveria ter lançado"
    except OSError:
        pass
