import os
import sys
import json
import hashlib
import hmac
from pathlib import Path
from unittest import mock

# env vars before module import
os.environ.setdefault("TELEGRAM_TOKEN", "fake_token")
os.environ.setdefault("SOL_CHAT_ID", "1030157568")
os.environ.setdefault("GROUP_CHAT_ID", "-1004472865546")
os.environ.setdefault("WEBHOOK_SECRET", "testsecret")

sys.path.insert(0, str(Path(__file__).parent.parent / "webhook"))

with mock.patch("dotenv.load_dotenv"):
    import importlib
    import receiver
    importlib.reload(receiver)

from fastapi.testclient import TestClient

client = TestClient(receiver.app)


def _signed(payload: bytes) -> str:
    return "sha256=" + hmac.new(b"testsecret", payload, hashlib.sha256).hexdigest()


def _push_payload(repo="nexus", branch="main", commits=None):
    if commits is None:
        commits = [{"message": "feat: add login", "url": "https://gh/c/1",
                    "timestamp": "2026-06-24T10:00:00Z"}]
    return {
        "ref": f"refs/heads/{branch}",
        "repository": {"name": repo},
        "pusher": {"name": "paulinett1508-dev"},
        "commits": commits,
        "compare": "https://gh/compare/abc...def",
    }


def _pr_payload(action="opened", merged=False):
    return {
        "action": action,
        "repository": {"name": "nexus"},
        "pull_request": {
            "number": 7,
            "title": "feat: nova auth",
            "html_url": "https://gh/pr/7",
            "user": {"login": "paulinett1508-dev"},
            "base": {"ref": "main"},
            "head": {"ref": "feature/auth"},
            "merged": merged,
            "merged_by": {"login": "paulinett1508-dev"} if merged else None,
        },
    }


# ── formatters (puras) ────────────────────────────────────────────────────────

def test_fmt_push_single_commit():
    msg = receiver._fmt_push(_push_payload())
    assert "nexus" in msg
    assert "main" in msg
    assert "add login" in msg


def test_fmt_push_strips_conventional_prefix():
    data = _push_payload(commits=[{"message": "feat(auth): add OAuth",
                                    "url": "u", "timestamp": ""}])
    msg = receiver._fmt_push(data)
    assert "feat(auth):" not in msg
    assert "add OAuth" in msg


def test_fmt_push_multiple_commits():
    commits = [
        {"message": f"fix: item {i}", "url": f"u{i}", "timestamp": ""}
        for i in range(3)
    ]
    msg = receiver._fmt_push(_push_payload(commits=commits))
    assert "· item" in msg  # prefix stripped, bullets present


def test_fmt_push_returns_none_for_tag():
    data = _push_payload()
    data["ref"] = "refs/tags/v1.0.0"
    assert receiver._fmt_push(data) is None


def test_fmt_push_returns_none_for_empty_commits():
    data = _push_payload(commits=[])
    assert receiver._fmt_push(data) is None


def test_fmt_pr_opened():
    msg = receiver._fmt_pr(_pr_payload("opened"))
    assert "PR #7" in msg
    assert "feature/auth" in msg
    assert "main" in msg


def test_fmt_pr_merged():
    msg = receiver._fmt_pr(_pr_payload("closed", merged=True))
    assert "mergeado" in msg
    assert "PR #7" in msg


def test_fmt_pr_closed_without_merge():
    msg = receiver._fmt_pr(_pr_payload("closed", merged=False))
    assert "❌" in msg
    assert "sem merge" in msg


def test_fmt_pr_reopened():
    msg = receiver._fmt_pr(_pr_payload("reopened"))
    assert "🔄" in msg


def test_fmt_pr_unknown_action():
    assert receiver._fmt_pr(_pr_payload("assigned")) is None


# ── routing — thread_id correto por evento ────────────────────────────────────

def test_push_routes_to_planetas_topic():
    payload = json.dumps(_push_payload()).encode()
    captured = {}

    def fake_send(text, thread_id=None):
        captured["thread_id"] = thread_id

    with mock.patch.object(receiver, "_send", side_effect=fake_send):
        resp = client.post("/webhook", content=payload,
                           headers={"X-GitHub-Event": "push",
                                    "X-Hub-Signature-256": _signed(payload)})
    assert resp.status_code == 200
    assert captured["thread_id"] == receiver.TOPIC_PLANETAS


def test_pr_routes_to_planetas_topic():
    payload = json.dumps(_pr_payload("opened")).encode()
    captured = {}

    def fake_send(text, thread_id=None):
        captured["thread_id"] = thread_id

    with mock.patch.object(receiver, "_send", side_effect=fake_send):
        resp = client.post("/webhook", content=payload,
                           headers={"X-GitHub-Event": "pull_request",
                                    "X-Hub-Signature-256": _signed(payload)})
    assert resp.status_code == 200
    assert captured["thread_id"] == receiver.TOPIC_PLANETAS


def test_unknown_event_does_not_send():
    payload = json.dumps({"repository": {"name": "nexus"}}).encode()
    called = []

    with mock.patch.object(receiver, "_send", side_effect=lambda *a, **kw: called.append(1)):
        client.post("/webhook", content=payload,
                    headers={"X-GitHub-Event": "star",
                             "X-Hub-Signature-256": _signed(payload)})
    assert not called


def test_invalid_signature_returns_401():
    payload = json.dumps(_push_payload()).encode()
    resp = client.post("/webhook", content=payload,
                       headers={"X-GitHub-Event": "push",
                                "X-Hub-Signature-256": "sha256=wrongsig"})
    assert resp.status_code == 401


# ── GROUP_CHAT_ID env var ─────────────────────────────────────────────────────

def test_send_uses_group_chat_id():
    """_send deve usar GROUP_CHAT_ID, não SOL_CHAT_ID."""
    assert receiver.GROUP_CHAT_ID == os.environ["GROUP_CHAT_ID"]
    assert receiver.GROUP_CHAT_ID != os.environ["SOL_CHAT_ID"]
