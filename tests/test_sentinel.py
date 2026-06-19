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
