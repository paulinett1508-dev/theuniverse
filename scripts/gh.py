#!/usr/bin/env python3
"""Cliente GitHub compartilhado — usado pelo Censo e pelo Sentinel.

Só stdlib. Token via env GITHUB_TOKEN ou .vault (local).
"""
import os
import sys
import json
import urllib.request
from pathlib import Path

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
SELF = "theuniverse"  # o observatório não é planeta


def token():
    t = os.getenv("GITHUB_TOKEN")
    if t:
        return t.strip()
    vault = ROOT / ".vault"
    if vault.exists():
        for line in vault.read_text(encoding="utf-8").splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit("ERRO: GITHUB_TOKEN ausente (env ou .vault).")


def api(path, tok):
    req = urllib.request.Request(
        path if path.startswith("http") else API + path,
        headers={"Authorization": f"token {tok}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "theuniverse-censo"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()), r.headers


def list_repos(tok, _api=None):
    _api = _api or api
    repos, page = [], 1
    while True:
        batch, _ = _api(f"/user/repos?per_page=100&page={page}&affiliation=owner", tok)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if r["name"] != SELF]
