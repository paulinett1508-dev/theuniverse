import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import deploy_health


def test_compute_events_deploy_falhou():
    state = {"last": {"alpha": {"id": 100, "state": "success"}}}
    current = {"alpha": {"id": 101, "state": "failure", "env": "production"}}
    events = deploy_health.compute_events(state, current)
    assert any(e["kind"] == "deploy_falhou" and e["repo"] == "alpha" for e in events)


def test_compute_events_sem_regressao_mesmo_id():
    state = {"last": {"alpha": {"id": 101, "state": "failure"}}}
    current = {"alpha": {"id": 101, "state": "failure", "env": "production"}}
    events = deploy_health.compute_events(state, current)
    assert events == []


def test_compute_events_recovery():
    state = {"last": {"alpha": {"id": 100, "state": "failure"}}}
    current = {"alpha": {"id": 101, "state": "success", "env": "production"}}
    events = deploy_health.compute_events(state, current)
    assert any(e["kind"] == "deploy_ok" and e["repo"] == "alpha" for e in events)


def test_compute_events_repo_novo_com_sucesso_nao_alerta():
    state = {"last": {}}
    current = {"alpha": {"id": 1, "state": "success", "env": "production"}}
    events = deploy_health.compute_events(state, current)
    assert events == []


def test_compute_events_repo_novo_com_falha_alerta():
    state = {"last": {}}
    current = {"alpha": {"id": 1, "state": "failure", "env": "production"}}
    events = deploy_health.compute_events(state, current)
    assert any(e["kind"] == "deploy_falhou" for e in events)


def test_format_event_falhou():
    ev = {"kind": "deploy_falhou", "repo": "alpha",
          "env": "production", "deployment_id": 101}
    txt = deploy_health.format_event(ev)
    assert "🚨" in txt and "alpha" in txt


def test_format_event_ok():
    ev = {"kind": "deploy_ok", "repo": "alpha",
          "env": "production", "deployment_id": 101}
    txt = deploy_health.format_event(ev)
    assert "✅" in txt and "alpha" in txt


def test_build_report_all_ok():
    report = deploy_health.build_report(checked=5, events=[])
    assert "✅" in report and "5" in report


def test_build_report_com_falha():
    events = [{"kind": "deploy_falhou", "repo": "alpha",
               "env": "production", "deployment_id": 101}]
    report = deploy_health.build_report(checked=3, events=events)
    assert "⚠️" in report
