"""Broadcast: cria issue em cada repo pedindo instalação dos commands /abrirsessao e /fecharsessao."""
import subprocess
import sys

OWNER = "paulinett1508-dev"

REPOS = [
    "bolaocopa2026",
    "centroculturalsbr",
    "CertiSYS",
    "contabilplus",
    "f1-pulse",
    "FinanceFlow",
    "flowdigitalstudio",
    "hqplus",
    "luna-base",
    "mcp-eventos",
    "nexus-labsobral",
    "sbrchecks",
    "sbrgestao",
    "sentinel-core",
    "sicefsus-sistema",
    "sigmed",
    "SuperCartolaManagerv5-production",
    "tokentown",
    "vibegaminghub",
]

TITLE = "chore(claude): adicionar commands /abrirsessao e /fecharsessao"

BODY = """\
## O quê

Novas skills de workflow foram adicionadas ao `agnostic-core`:
- `/abrirsessao` — reconstrói contexto completo da sessão anterior em < 60s (substitui `/newsession`)
- `/fecharsessao` — encerramento robusto: git audit, issues, handoff, memórias

## Por quê

Padronizar abertura/fechamento de sessão em todos os repos do ecossistema. \
Zero limbo entre sessões.

## Done

- [ ] Atualizar o submodule: `git submodule update --remote .agnostic-core`
- [ ] Criar `.claude/commands/abrirsessao.md` invocando a skill do agnostic-core com adaptações do repo
- [ ] Criar `.claude/commands/fecharsessao.md` idem

**Referência:** skills em `.agnostic-core/skills/workflow/abrirsessao.md` e `fecharsessao.md`
Exemplo de implementação: `theuniverse/.claude/commands/`
"""


def create_issue(repo: str) -> bool:
    result = subprocess.run(
        [
            "gh", "issue", "create",
            "--repo", f"{OWNER}/{repo}",
            "--title", TITLE,
            "--label", "task",
            "--body", BODY,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        print(f"  ✓ {repo}: {url}")
        return True
    else:
        err = result.stderr.strip()
        # label não existe no repo? tentar sem label
        if "label" in err.lower():
            result2 = subprocess.run(
                [
                    "gh", "issue", "create",
                    "--repo", f"{OWNER}/{repo}",
                    "--title", TITLE,
                    "--body", BODY,
                ],
                capture_output=True,
                text=True,
            )
            if result2.returncode == 0:
                url = result2.stdout.strip()
                print(f"  ✓ {repo} (sem label): {url}")
                return True
            err = result2.stderr.strip()
        print(f"  ✗ {repo}: {err}", file=sys.stderr)
        return False


def main():
    print(f"Broadcast para {len(REPOS)} repos...\n")
    ok = 0
    fail = 0
    for repo in REPOS:
        if create_issue(repo):
            ok += 1
        else:
            fail += 1
    print(f"\nResultado: {ok} ✓ / {fail} ✗")


if __name__ == "__main__":
    main()
