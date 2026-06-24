import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pulso


def _r(url, ok, status=200, latency=100, repo="test-repo"):
    return {"url": url, "ok": ok, "status": status, "latency_ms": latency, "repo": repo}


def test_compute_events_url_caiu():
    state = {"status": {"https://a.com": True}}
    results = [_r("https://a.com", ok=False, status=0, latency=10000)]
    events = pulso.compute_events(state, results)
    assert len(events) == 1 and events[0]["kind"] == "url_caiu"


def test_compute_events_url_voltou():
    state = {"status": {"https://a.com": False}}
    results = [_r("https://a.com", ok=True, status=200, latency=120)]
    events = pulso.compute_events(state, results)
    assert len(events) == 1 and events[0]["kind"] == "url_voltou"


def test_compute_events_sem_mudanca():
    state = {"status": {"https://a.com": True}}
    results = [_r("https://a.com", ok=True, status=200, latency=80)]
    assert pulso.compute_events(state, results) == []


def test_compute_events_nova_url_cai_alerta():
    state = {"status": {}}
    results = [_r("https://novo.com", ok=False, status=503, latency=200)]
    events = pulso.compute_events(state, results)
    assert any(e["kind"] == "url_caiu" for e in events)


def test_format_event_caiu():
    ev = {"kind": "url_caiu", "url": "https://a.com", "status": 0, "latency_ms": 10000, "repo": "x"}
    txt = pulso.format_event(ev)
    assert "🔴" in txt and "caiu" in txt


def test_format_event_voltou():
    ev = {"kind": "url_voltou", "url": "https://a.com", "status": 200, "latency_ms": 120, "repo": "x"}
    txt = pulso.format_event(ev)
    assert "🟢" in txt and "voltou" in txt


def test_build_report_all_up():
    results = [_r("https://a.com", ok=True)]
    report = pulso.build_report(results, [])
    assert "✅" in report and "1" in report


def test_build_report_com_eventos():
    results = [_r("https://a.com", ok=False, status=503, latency=5000)]
    events = [{"kind": "url_caiu", "url": "https://a.com", "status": 503,
               "latency_ms": 5000, "repo": "x"}]
    report = pulso.build_report(results, events)
    assert "⚠️" in report


def test_filter_urls_extrai_validas():
    repos = [
        {"name": "alpha", "homepage": "https://alpha.vercel.app"},
        {"name": "beta",  "homepage": ""},
        {"name": "gamma", "homepage": None},
        {"name": "delta", "homepage": "http://delta.com"},
    ]
    result = pulso.filter_urls(repos)
    assert len(result) == 2
    assert all(u["url"].startswith("http") for u in result)
