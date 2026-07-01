#!/usr/bin/env python3
"""
Workspace — materializa o clone físico de cada planeta em
D:\\theuniverse\\corpos\\<cinturão>\\<cluster>\\<repo>.

Fonte de verdade: censo.py (NATUREZA, CLUSTERS) + GitHub API (list_repos).
Idempotente: só clona o que falta, nunca deleta, nunca sobrescreve.
Token nunca fica gravado em .git/config — usado só na hora do clone.

Escopo: só cinturão kuiper (órbita privada/individual). Os cinturões
profissionais (gould, van-allen) já têm local canônico de clone fora do
theuniverse — não são duplicados aqui.

Uso:
  python scripts/workspace.py            # clona o que faltar (kuiper)
  python scripts/workspace.py --dry-run  # só mostra o plano
"""
import argparse
import subprocess
import sys

from gh import ROOT, token_for, list_repos, token
from censo import NATUREZA, CLUSTERS, EXCLUDE

CORPOS = ROOT / "corpos"
ESCOPO = {"kuiper"}


def slot_for(repo):
    name = repo["name"]
    cinturao = NATUREZA.get(name, "nao-classificado")
    cluster = CLUSTERS.get(name, "nao-classificado")
    return CORPOS / cinturao / cluster / name


def clone(repo, dest):
    owner = repo["full_name"].split("/")[0]
    tok = token_for(owner)
    auth_url = repo["clone_url"].replace("https://", f"https://x-access-token:{tok}@")
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--quiet", auth_url, str(dest)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"     ⚠️ falha ao clonar {repo['full_name']}: {result.stderr.strip()[:200]}")
        return False
    subprocess.run(["git", "-C", str(dest), "remote", "set-url", "origin", repo["clone_url"]])
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tok = token()
    repos = [r for r in list_repos(tok)
             if r["name"] not in EXCLUDE and NATUREZA.get(r["name"]) in ESCOPO]
    plan = sorted(((r, slot_for(r)) for r in repos), key=lambda x: x[0]["name"].lower())
    faltando = [(r, d) for r, d in plan if not d.exists()]

    print(f"Workspace: {len(plan)} planetas | {len(plan) - len(faltando)} já clonados | {len(faltando)} a clonar")

    if args.dry_run:
        for r, d in faltando:
            print(f"  ⏳ {r['name']} → {d.relative_to(ROOT)}")
        return 0

    ok = 0
    for r, dest in faltando:
        print(f"  📡 clonando {r['full_name']} → {dest.relative_to(ROOT)}")
        if clone(r, dest):
            ok += 1
    print(f"Workspace sincronizado: {ok}/{len(faltando)} clonados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
