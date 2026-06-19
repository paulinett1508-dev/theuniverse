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
