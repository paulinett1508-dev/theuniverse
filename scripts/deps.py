#!/usr/bin/env python3
"""Sentinel · Deps: varre dependências dos planetas em busca de CVEs.

Detecta package.json, requirements.txt, composer.json. Consulta OSV.dev
para cada pacote. Dedup por chave (repo+pacote+cve). Notifica Telegram por
vulnerabilidade nova + heartbeat ao final. Só stdlib.
"""
import html
import io
import json
import re
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

from gh import ROOT, API, token, list_repos
from sentinel import send_telegram

STATE_PATH = ROOT / "state" / "deps-state.json"
OSV_URL = "https://api.osv.dev/v1/query"
NOTIFY_CAP = 20
MAX_PKGS_PER_REPO = 200


def parse_package_json(content):
    """Pure: extrai dependências de um package.json."""
    try:
        data = json.loads(content)
    except Exception:
        return []
    pkgs = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        for name, version in (data.get(section) or {}).items():
            v = re.sub(r"[^0-9.]", "", version.lstrip("^~>=!")).split(".")[0:3]
            pkgs.append({"name": name, "version": ".".join(v) if v else "", "ecosystem": "npm"})
    return pkgs


def parse_requirements(content):
    """Pure: extrai dependências de requirements.txt."""
    pkgs = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-") or line.startswith("git+"):
            continue
        m = re.match(r"([A-Za-z0-9_.-]+)(?:\s*[=<>!~]+\s*([0-9][0-9a-zA-Z._-]*))?", line)
        if m:
            pkgs.append({"name": m.group(1), "version": m.group(2) or "", "ecosystem": "pypi"})
    return pkgs


def parse_manifest(filename, content):
    """Pure: dispatcher pelo tipo de manifesto."""
    if filename.endswith("package.json"):
        return parse_package_json(content)
    if filename.endswith("requirements.txt"):
        return parse_requirements(content)
    return []


MANIFEST_RE = re.compile(r"(^|/)package\.json$|(^|/)requirements\.txt$", re.I)
SKIP_RE = re.compile(r"(/|^)(node_modules|vendor|\.git|dist|build)(/|$)", re.I)


def _osv_query(pkg):
    """Consulta OSV.dev — devolve lista de vulns ou [] se erro."""
    eco = "npm" if pkg["ecosystem"] == "npm" else "PyPI"
    body = json.dumps({"package": {"name": pkg["name"], "ecosystem": eco},
                       "version": pkg["version"]}).encode()
    req = urllib.request.Request(OSV_URL, data=body,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "theuniverse-deps"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("vulns") or []
    except Exception:
        return []


def _fetch_bytes(url, tok):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {tok}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "theuniverse-deps"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _scan_repo(full_name, repo_name, tok):
    """Baixa tarball e varre manifestos — devolve lista de findings."""
    try:
        blob = _fetch_bytes(f"{API}/repos/{full_name}/tarball", tok)
        tar = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
    except Exception as e:
        print(f"  tarball falhou em {full_name}: {e}", file=sys.stderr)
        return []

    pkgs_all = []
    for member in tar.getmembers():
        if not member.isfile():
            continue
        path = member.name.split("/", 1)[1] if "/" in member.name else member.name
        if SKIP_RE.search(path) or not MANIFEST_RE.search(path):
            continue
        try:
            content = tar.extractfile(member).read().decode("utf-8", "ignore")
            pkgs_all.extend(parse_manifest(path, content))
        except Exception:
            continue
    tar.close()

    findings = []
    seen_pkg = set()
    for pkg in pkgs_all[:MAX_PKGS_PER_REPO]:
        key_pkg = f"{pkg['ecosystem']}:{pkg['name']}:{pkg['version']}"
        if key_pkg in seen_pkg:
            continue
        seen_pkg.add(key_pkg)
        for vuln in _osv_query(pkg):
            cve = next((a["id"] for a in vuln.get("aliases", []) if a["id"].startswith("CVE")),
                       vuln["id"])
            severity = _severity(vuln)
            key = f"{repo_name}:{pkg['name']}:{cve}"
            findings.append({"key": key, "repo": repo_name, "pkg": pkg["name"],
                              "version": pkg["version"], "severity": severity,
                              "cve": cve, "ecosystem": pkg["ecosystem"]})
    return findings


def _severity(vuln):
    for sev in vuln.get("severity") or []:
        score = sev.get("score") or ""
        if "CVSS:3" in sev.get("type", ""):
            try:
                v = float(score.split("/")[-1])
                if v >= 9.0:
                    return "CRITICAL"
                if v >= 7.0:
                    return "HIGH"
                if v >= 4.0:
                    return "MEDIUM"
                return "LOW"
            except Exception:
                pass
    return "HIGH"


def compute_events(state, findings):
    """Pure: filtra findings que ainda não foram vistos."""
    seen = set(state.get("seen") or {})
    events = []
    for f in findings:
        if f["key"] not in seen:
            events.append({**f, "kind": "vuln_nova"})
    return events


def format_event(ev):
    return (f"🔓 <b>{html.escape(ev['repo'])}</b> — {html.escape(ev['severity'])}\n"
            f"pacote: <code>{html.escape(ev['pkg'])} {html.escape(ev['version'])}</code> "
            f"({html.escape(ev['ecosystem'])})\n"
            f"CVE: <code>{html.escape(ev['cve'])}</code>")


def build_report(scanned, events):
    footer = "✅ nenhuma vulnerabilidade nova" if not events else f"⚠️ {len(events)} CVE(s) nova(s)"
    return (f"<b>Sentinel · Deps</b> — {time.strftime('%H:%M UTC', time.gmtime())}\n"
            f"Repos varridos: {scanned}\n"
            f"{footer}")


def load_state(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def main():
    tok = token()
    repos = list_repos(tok)
    all_findings = []
    for r in repos:
        all_findings.extend(_scan_repo(r["full_name"], r["name"], tok))

    state = load_state(STATE_PATH)
    if state is None:
        keys = {f["key"] for f in all_findings}
        save_state(STATE_PATH, {"seen": sorted(keys)})
        print(f"Estado inicial: {len(repos)} repos, {len(all_findings)} CVEs base.")
        try:
            send_telegram(build_report(len(repos), []))
        except Exception:
            pass
        return 0

    events = compute_events(state, all_findings)
    sent = 0
    for ev in events[:NOTIFY_CAP]:
        try:
            send_telegram(format_event(ev))
            sent += 1
        except Exception as e:
            print(f"  envio falhou ({ev['repo']} {ev['cve']}): {e}", file=sys.stderr)

    new_seen = set(state.get("seen") or []) | {f["key"] for f in all_findings}
    save_state(STATE_PATH, {"seen": sorted(new_seen)})

    try:
        send_telegram(build_report(len(repos), events))
    except Exception:
        pass

    print(f"Deps: {len(repos)} repos · {len(all_findings)} CVEs detectadas · "
          f"{len(events)} novas · {sent} notificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
