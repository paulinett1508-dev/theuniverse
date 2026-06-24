import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import deps


def test_parse_package_json_extracts_deps():
    content = '{"dependencies": {"express": "4.18.2"}, "devDependencies": {"jest": "29.0.0"}}'
    pkgs = deps.parse_package_json(content)
    names = [p["name"] for p in pkgs]
    assert "express" in names and "jest" in names
    assert all(p["ecosystem"] == "npm" for p in pkgs)


def test_parse_package_json_version():
    content = '{"dependencies": {"lodash": "4.17.20"}}'
    pkgs = deps.parse_package_json(content)
    assert pkgs[0]["version"] == "4.17.20"


def test_parse_package_json_invalid_json():
    pkgs = deps.parse_package_json("not json {{{")
    assert pkgs == []


def test_parse_requirements_extracts_packages():
    content = "flask==2.3.0\nrequests>=2.28.0\n# comment\nnumpy\n"
    pkgs = deps.parse_requirements(content)
    names = [p["name"] for p in pkgs]
    assert "flask" in names and "requests" in names and "numpy" in names


def test_parse_requirements_version_pinned():
    content = "django==4.2.1\n"
    pkgs = deps.parse_requirements(content)
    assert pkgs[0]["version"] == "4.2.1"


def test_parse_requirements_skips_comments_and_empty():
    content = "# comment\n\nflask==2.0.0\n"
    pkgs = deps.parse_requirements(content)
    assert len(pkgs) == 1


def test_parse_requirements_ecosystem():
    pkgs = deps.parse_requirements("flask==2.0.0\n")
    assert pkgs[0]["ecosystem"] == "pypi"


def test_compute_events_new_vuln():
    state = {"seen": {}}
    findings = [{"key": "abc123", "repo": "alpha", "pkg": "lodash",
                 "version": "4.17.20", "severity": "HIGH",
                 "cve": "CVE-2021-23337", "ecosystem": "npm"}]
    events = deps.compute_events(state, findings)
    assert len(events) == 1 and events[0]["kind"] == "vuln_nova"


def test_compute_events_no_duplicate():
    state = {"seen": {"abc123": True}}
    findings = [{"key": "abc123", "repo": "alpha", "pkg": "lodash",
                 "version": "4.17.20", "severity": "HIGH",
                 "cve": "CVE-2021-23337", "ecosystem": "npm"}]
    events = deps.compute_events(state, findings)
    assert events == []


def test_format_event_vuln():
    ev = {"kind": "vuln_nova", "repo": "alpha", "pkg": "lodash",
          "version": "4.17.20", "severity": "HIGH",
          "cve": "CVE-2021-23337", "ecosystem": "npm"}
    txt = deps.format_event(ev)
    assert "🔓" in txt and "lodash" in txt and "CVE-2021-23337" in txt


def test_build_report_clean():
    report = deps.build_report(scanned=3, events=[])
    assert "✅" in report and "3" in report


def test_build_report_com_vulns():
    events = [{"kind": "vuln_nova", "repo": "alpha", "pkg": "x",
               "version": "1.0.0", "severity": "HIGH",
               "cve": "CVE-1234-5678", "ecosystem": "npm"}]
    report = deps.build_report(scanned=2, events=events)
    assert "⚠️" in report
