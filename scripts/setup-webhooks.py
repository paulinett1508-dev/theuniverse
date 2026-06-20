"""Registra/atualiza o webhook do Universe Receiver em todos os repos do universo."""
import json
import sys
import urllib.error
import urllib.request

# ── config ────────────────────────────────────────────────────────────────────

WEBHOOK_URL = "http://195.200.5.145:9120/webhook"
EVENTS = ["push", "pull_request"]

UNIVERSE_OWNERS = {"paulinett1508-dev", "Lab-Sobral-Dev"}
EXCLUDE = {"the-matrix", "matrix-core", "baileys-whatsapp-server", "bitrix-buddy-chat",
           "theuniverse"}

# ── vault ─────────────────────────────────────────────────────────────────────

def _load_vault(path=".vault"):
    v = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, val = line.split("=", 1)
                v[k.strip()] = val.strip()
    return v


# ── github api ────────────────────────────────────────────────────────────────

def _api(path: str, token: str, method="GET", body=None):
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        return json.loads(body_txt) if body_txt else {}, e.code


def _list_repos(token: str) -> list[dict]:
    repos, page = [], 1
    while True:
        batch, _ = _api(f"/user/repos?per_page=100&page={page}", token)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    seen, result = set(), []
    for r in repos:
        owner = r["full_name"].split("/")[0]
        key = r["full_name"]
        if r["name"] not in EXCLUDE and owner in UNIVERSE_OWNERS and key not in seen:
            seen.add(key)
            result.append(r)
    return result


def _get_hooks(repo_full: str, token: str) -> list[dict]:
    hooks, _ = _api(f"/repos/{repo_full}/hooks", token)
    return hooks if isinstance(hooks, list) else []


def _create_hook(repo_full: str, token: str, secret: str) -> tuple[dict, int]:
    return _api(f"/repos/{repo_full}/hooks", token, method="POST", body={
        "name": "web",
        "active": True,
        "events": EVENTS,
        "config": {
            "url": WEBHOOK_URL,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0",
        },
    })


def _update_hook(repo_full: str, hook_id: int, token: str, secret: str) -> tuple[dict, int]:
    return _api(f"/repos/{repo_full}/hooks/{hook_id}", token, method="PATCH", body={
        "active": True,
        "events": EVENTS,
        "config": {
            "url": WEBHOOK_URL,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0",
        },
    })


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    vault = _load_vault()
    token = vault.get("GITHUB_TOKEN", "")
    secret = vault.get("WEBHOOK_SECRET", "")

    if not token:
        print("ERRO: GITHUB_TOKEN ausente no .vault", file=sys.stderr)
        sys.exit(1)
    if not secret:
        print("ERRO: WEBHOOK_SECRET ausente no .vault", file=sys.stderr)
        sys.exit(1)

    dry = "--dry-run" in sys.argv
    if dry:
        print("[DRY-RUN] nenhuma alteracao sera feita\n")

    repos = _list_repos(token)
    print(f"{len(repos)} repos no universo\n")

    ok = created = updated = skipped = errors = 0

    for r in repos:
        full = r["full_name"]
        hooks = _get_hooks(full, token)
        existing = next(
            (h for h in hooks if h.get("config", {}).get("url") == WEBHOOK_URL), None
        )

        if existing:
            if dry:
                print(f"  ~ {full}  (existente, id={existing['id']})")
                skipped += 1
                continue
            _, status = _update_hook(full, existing["id"], token, secret)
            if status in (200, 204):
                print(f"  ~ {full}  atualizado")
                updated += 1
            else:
                print(f"  ! {full}  update falhou (HTTP {status})")
                errors += 1
        else:
            if dry:
                print(f"  + {full}  (sera criado)")
                created += 1
                continue
            _, status = _create_hook(full, token, secret)
            if status == 201:
                print(f"  + {full}  criado")
                created += 1
            else:
                print(f"  ! {full}  criacao falhou (HTTP {status})")
                errors += 1

    print(f"\ncriados={created}  atualizados={updated}  "
          f"sem-alteracao={skipped}  erros={errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
