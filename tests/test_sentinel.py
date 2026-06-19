import sys
import json
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
    }
    state = sentinel.seed_state(snapshot)
    assert state["known_repos"] == ["alpha", "beta"]
    assert state["last_run_id"] == {"alpha": 100}      # beta sem run → ausente
    assert state["last_issue_number"] == {"alpha": 5}  # maior número; beta sem issue → ausente


def _snapshot(repos, latest_run=None, issues=None):
    return {
        "repos": repos,
        "latest_run": latest_run or {r: None for r in repos},
        "issues": issues or {r: [] for r in repos},
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
