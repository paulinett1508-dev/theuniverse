#!/usr/bin/env python3
"""Sistema Nervoso (subsistema B): poll da API → eventos → Telegram.

Roda no theuniverse via GitHub Actions. Só observação (leitura). O único
git push é do próprio estado. Reusa o cliente de gh.py.
"""
import os
import sys
import json
import copy
import urllib.request
import urllib.parse
from pathlib import Path

from gh import ROOT, token, api, list_repos

STATE_PATH = ROOT / "state" / "sentinel-state.json"

_EMOJI = {
    "novo_planeta": "🆕",
    "planeta_sumido": "💥",
    "ci_falhou": "🔴",
    "issue_nova": "🚨",
}


def load_state(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seed_state(snapshot):
    last_run_id = {r: run["id"] for r, run in snapshot["latest_run"].items() if run}
    last_issue = {}
    for r, issues in snapshot["issues"].items():
        if issues:
            last_issue[r] = max(i["number"] for i in issues)
    return {
        "known_repos": list(snapshot["repos"]),
        "last_run_id": last_run_id,
        "last_issue_number": last_issue,
    }


def compute_events(state, snapshot):
    events = []
    known = set(state["known_repos"])
    cur = set(snapshot["repos"])

    for r in sorted(cur - known):
        events.append({"kind": "novo_planeta", "repo": r})
    for r in sorted(known - cur):
        events.append({"kind": "planeta_sumido", "repo": r})

    for r in sorted(cur & known):
        run = snapshot["latest_run"].get(r)
        if (run and run["conclusion"] == "failure"
                and run["id"] != state["last_run_id"].get(r)):
            events.append({"kind": "ci_falhou", "repo": r,
                           "run_id": run["id"], "detail": run.get("name", "")})
        baseline = state["last_issue_number"].get(r, 0)
        for issue in sorted(snapshot["issues"].get(r, []), key=lambda i: i["number"]):
            if issue["number"] > baseline:
                events.append({"kind": "issue_nova", "repo": r,
                               "number": issue["number"], "detail": issue["title"]})
    return events


def apply_event(state, event, snapshot):
    s = copy.deepcopy(state)
    kind, repo = event["kind"], event["repo"]
    if kind == "novo_planeta":
        if repo not in s["known_repos"]:
            s["known_repos"].append(repo)
        run = snapshot["latest_run"].get(repo)
        if run:
            s["last_run_id"][repo] = run["id"]
        issues = snapshot["issues"].get(repo, [])
        if issues:
            s["last_issue_number"][repo] = max(i["number"] for i in issues)
    elif kind == "planeta_sumido":
        if repo in s["known_repos"]:
            s["known_repos"].remove(repo)
    elif kind == "ci_falhou":
        s["last_run_id"][repo] = event["run_id"]
    elif kind == "issue_nova":
        s["last_issue_number"][repo] = max(s["last_issue_number"].get(repo, 0), event["number"])
    return s


def format_event(event):
    emoji = _EMOJI[event["kind"]]
    repo = event["repo"]
    if event["kind"] == "novo_planeta":
        return f"{emoji} Novo planeta detectado: *{repo}*"
    if event["kind"] == "planeta_sumido":
        return f"{emoji} Planeta sumiu do GitHub: *{repo}*"
    if event["kind"] == "ci_falhou":
        return f"{emoji} CI falhou em *{repo}* (run {event['run_id']})"
    if event["kind"] == "issue_nova":
        return f"{emoji} Issue nova em *{repo}* #{event['number']}: {event['detail']}"
    return f"Evento em {repo}"
