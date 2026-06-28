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
# owners cujos repos entram no universo
UNIVERSE_OWNERS = {"paulinett1508-dev", "Lab-Sobral-Dev"}

# mapeamento owner → chave no .vault / env
_OWNER_TOKEN_KEYS = {
    "paulinett1508-dev": "GITHUB_TOKEN",
    "Lab-Sobral-Dev":    "GITHUB_TOKEN_LAB",
}


def _read_vault():
    vault = ROOT / ".vault"
    data = {}
    if vault.exists():
        for line in vault.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def token():
    """Token primário (paulinett1508-dev) — compatibilidade retroativa."""
    t = os.getenv("GITHUB_TOKEN") or _read_vault().get("GITHUB_TOKEN")
    if not t:
        sys.exit("ERRO: GITHUB_TOKEN ausente (env ou .vault).")
    return t.strip()


def all_tokens():
    """Retorna dict owner → token para todas as contas do universo."""
    vault = _read_vault()
    result = {}
    for owner, key in _OWNER_TOKEN_KEYS.items():
        t = os.getenv(key) or vault.get(key)
        if t:
            result[owner] = t.strip()
    if not result:
        sys.exit("ERRO: nenhum token encontrado no vault.")
    return result


def token_for(owner):
    """Token correto para um owner específico."""
    return all_tokens().get(owner, token())


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


def list_repos(tok=None, _api=None):
    """Varre todas as contas do universo e retorna repos únicos."""
    _api = _api or api
    seen, result = set(), []
    for owner, owner_tok in all_tokens().items():
        page = 1
        while True:
            batch, _ = _api(
                f"/user/repos?per_page=100&page={page}&visibility=all&affiliation=owner",
                owner_tok,
            )
            if not batch:
                break
            for r in batch:
                repo_owner = r["full_name"].split("/")[0]
                key = r["full_name"]
                if r["name"] != SELF and repo_owner in UNIVERSE_OWNERS and key not in seen:
                    seen.add(key)
                    result.append(r)
            page += 1
    return result
