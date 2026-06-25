import sys
import json
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import sentinel


def test_load_state_missing_returns_none(tmp_path):
    assert sentinel.load_state(tmp_path / "nope.json") is None


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    state = {"known_repos": ["a"], "last_run_id": {"a": 7}, "last_issue_number": {"a": 3}}
    sentinel.save_state(p, state)
    assert sentinel.load_state(p) == state


def test_seed_state_from_snapshot():
    snapshot = {
        "repos": ["alpha", "beta"],
        "latest_run": {"alpha": {"id": 100, "conclusion": "success"}, "beta": None},
        "issues": {"alpha": [{"number": 5, "title": "x"}, {"number": 2, "title": "y"}], "beta": []},
        "secrets": {"alpha": [], "beta": []},
    }
    state = sentinel.seed_state(snapshot)
    assert state["known_repos"] == ["alpha", "beta"]
    assert state["last_run_id"] == {"alpha": 100}      # beta sem run → ausente
    assert state["last_issue_number"] == {"alpha": 5}  # maior número; beta sem issue → ausente


def _snapshot(repos, latest_run=None, issues=None, secrets=None):
    return {
        "repos": repos,
        "latest_run": latest_run or {r: None for r in repos},
        "issues": issues or {r: [] for r in repos},
        "secrets": secrets or {r: [] for r in repos},
    }


def test_compute_events_novo_e_sumido():
    state = {"known_repos": ["alpha"], "last_run_id": {}, "last_issue_number": {}}
    snap = _snapshot(["alpha", "beta"])
    events = sentinel.compute_events(state, snap)
    kinds = {(e["kind"], e["repo"]) for e in events}
    assert ("novo_planeta", "beta") in kinds
    snap2 = _snapshot(["beta"])
    events2 = sentinel.compute_events(state, snap2)
    assert ("planeta_sumido", "alpha") in {(e["kind"], e["repo"]) for e in events2}


def test_compute_events_ci_falhou_so_em_novo_run():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {}}
    snap_fail = _snapshot(["alpha"], latest_run={"alpha": {"id": 11, "conclusion": "failure"}})
    assert any(e["kind"] == "ci_falhou" and e["run_id"] == 11
               for e in sentinel.compute_events(state, snap_fail))
    # mesmo run id já visto → não dispara
    state_seen = {"known_repos": ["alpha"], "last_run_id": {"alpha": 11}, "last_issue_number": {}}
    assert not any(e["kind"] == "ci_falhou" for e in sentinel.compute_events(state_seen, snap_fail))
    # run novo mas com sucesso → não dispara
    snap_ok = _snapshot(["alpha"], latest_run={"alpha": {"id": 12, "conclusion": "success"}})
    assert not any(e["kind"] == "ci_falhou" for e in sentinel.compute_events(state, snap_ok))


def test_compute_events_issue_nova_acima_do_baseline():
    state = {"known_repos": ["alpha"], "last_run_id": {}, "last_issue_number": {"alpha": 4}}
    snap = _snapshot(["alpha"], issues={"alpha": [{"number": 5, "title": "bug"}, {"number": 3, "title": "velha"}]})
    events = sentinel.compute_events(state, snap)
    nums = [e["number"] for e in events if e["kind"] == "issue_nova"]
    assert nums == [5]  # só a 5 (> baseline 4); a 3 ignorada


def test_apply_event_novo_planeta_silencia_historico():
    state = {"known_repos": [], "last_run_id": {}, "last_issue_number": {}}
    snap = _snapshot(["beta"], latest_run={"beta": {"id": 9, "conclusion": "failure"}},
                     issues={"beta": [{"number": 2, "title": "x"}]})
    ev = {"kind": "novo_planeta", "repo": "beta"}
    new = sentinel.apply_event(state, ev, snap)
    assert "beta" in new["known_repos"]
    assert new["last_run_id"]["beta"] == 9      # baseline silencioso
    assert new["last_issue_number"]["beta"] == 2


def test_apply_event_ci_e_issue_avancam_estado():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {"alpha": 4}}
    snap = _snapshot(["alpha"])
    s1 = sentinel.apply_event(state, {"kind": "ci_falhou", "repo": "alpha", "run_id": 11, "detail": "CI"}, snap)
    assert s1["last_run_id"]["alpha"] == 11
    s2 = sentinel.apply_event(s1, {"kind": "issue_nova", "repo": "alpha", "number": 6, "detail": "bug"}, snap)
    assert s2["last_issue_number"]["alpha"] == 6


def test_apply_event_planeta_sumido_remove():
    state = {"known_repos": ["alpha", "beta"], "last_run_id": {}, "last_issue_number": {}}
    new = sentinel.apply_event(state, {"kind": "planeta_sumido", "repo": "beta"}, _snapshot(["alpha"]))
    assert new["known_repos"] == ["alpha"]


def test_format_event_has_emoji_and_repo():
    txt = sentinel.format_event({"kind": "ci_falhou", "repo": "alpha", "run_id": 1, "detail": "build"})
    assert "🔴" in txt and "alpha" in txt


def test_notify_avanca_so_em_envio_ok():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {}}
    snap = _snapshot(["alpha"])
    events = [
        {"kind": "ci_falhou", "repo": "alpha", "run_id": 11, "detail": "x"},
        {"kind": "issue_nova", "repo": "alpha", "number": 5, "detail": "y"},
    ]
    sent = []

    def send_fn(text, thread_id=None):
        sent.append(text)
        if "🚨" in text:
            raise RuntimeError("telegram caiu")

    new_state, count = sentinel.notify(events, state, snap, send_fn)
    assert count == 1                                   # só o CI foi
    assert new_state["last_run_id"]["alpha"] == 11      # CI avançou
    assert "alpha" not in new_state["last_issue_number"]  # issue NÃO avançou → re-tenta


# --- Heartbeat ---

def test_build_heartbeat_report_clean_cycle():
    report = sentinel.build_heartbeat_report(["alpha", "beta", "gamma"], [])
    assert "3" in report
    assert "UTC" in report
    assert "✅" in report
    assert "Tudo limpo" in report


def test_build_heartbeat_report_with_events():
    events = [
        {"type": "ci_falhou", "repo": "alpha", "detail": "build"},
        {"type": "issue_nova", "repo": "beta", "detail": "bug X"},
    ]
    report = sentinel.build_heartbeat_report(["alpha", "beta"], events)
    assert "2" in report
    assert "🔴" in report
    assert "🚨" in report
    assert "alpha" in report
    assert "⚠️" in report
    assert "Ciclo concluído" in report


def test_build_heartbeat_report_all_event_emojis():
    events = [
        {"type": "ci_falhou",    "repo": "r1", "detail": "x"},
        {"type": "issue_nova",   "repo": "r2", "detail": "x"},
        {"type": "secret_exposto", "repo": "r3", "detail": "x"},
        {"type": "novo_planeta", "repo": "r4", "detail": "x"},
        {"type": "planeta_sumido", "repo": "r5", "detail": "x"},
    ]
    report = sentinel.build_heartbeat_report(["r1", "r2", "r3", "r4", "r5"], events)
    for emoji in ["🔴", "🚨", "🔑", "🆕", "💥"]:
        assert emoji in report


def test_send_heartbeat_silent_on_failure(monkeypatch):
    def raise_always(*a, **kw):
        raise OSError("sem rede")
    monkeypatch.setattr(urllib.request, "urlopen", raise_always)
    sentinel.send_heartbeat("bad_token", "123", "<b>ok</b>")


# ── build_universe_snapshot ───────────────────────────────────────────────────

def test_build_universe_snapshot_contains_repos():
    state = {"known_repos": ["nexus", "matrix-core"],
             "last_run_id": {"nexus": 42}, "last_issue_number": {"nexus": 3}}
    snap = sentinel.build_universe_snapshot(state, [])
    text = snap.decode("utf-8")
    assert "nexus" in text
    assert "matrix-core" in text


def test_build_universe_snapshot_lists_events():
    state = {"known_repos": ["nexus"], "last_run_id": {}, "last_issue_number": {}}
    events = [{"type": "ci_falhou", "repo": "nexus", "detail": "build"}]
    text = sentinel.build_universe_snapshot(state, events).decode("utf-8")
    assert "ci_falhou" in text or "CI" in text or "nexus" in text


def test_build_universe_snapshot_returns_bytes():
    state = {"known_repos": [], "last_run_id": {}, "last_issue_number": {}}
    result = sentinel.build_universe_snapshot(state, [])
    assert isinstance(result, bytes)


# ── send_document ─────────────────────────────────────────────────────────────

def test_send_document_posts_multipart(monkeypatch):
    captured = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["ct"] = req.get_header("Content-type")
        captured["body"] = req.data
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    sentinel.send_document("tok", "-123", "snap.txt", b"hello world",
                           caption="test", thread_id=16)

    assert "sendDocument" in captured["url"]
    assert "multipart/form-data" in captured["ct"]
    assert b"snap.txt" in captured["body"]
    assert b"hello world" in captured["body"]
    assert b"-123" in captured["body"]
    assert b"16" in captured["body"]


def test_send_document_silent_on_failure(monkeypatch):
    def raise_always(*a, **kw):
        raise OSError("sem rede")
    monkeypatch.setattr(urllib.request, "urlopen", raise_always)
    sentinel.send_document("bad", "123", "f.txt", b"x")  # não deve lançar
