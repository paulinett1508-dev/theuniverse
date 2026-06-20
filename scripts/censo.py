#!/usr/bin/env python3
"""
Censo do Universo — observa todos os planetas (repos) e atualiza o registro.

Fluxo: leitura-only via API → atualiza planets/ + _index.md + CHANGELOG.md.
NUNCA escreve em outro repo. O único git afetado é o theuniverse.

Token: env GITHUB_TOKEN (no Actions = secret UNIVERSE_PAT; local = do .vault).
Uso:
  python scripts/censo.py            # detecta e aplica mudanças
  python scripts/censo.py --dry-run  # só reporta, não escreve
"""
import sys
import base64
import argparse
from datetime import datetime, timezone

from gh import API, ROOT, SELF, token, api, list_repos

PLANETS = ROOT / "planets"
CHANGELOG = ROOT / "CHANGELOG.md"

# Repos excluídos do universo (decisão do Sol)
EXCLUDE = {
    "the-matrix", "matrix-core", "baileys-whatsapp-server", "bitrix-buddy-chat",
    "agnvendas-painelsbr",  # arquivado — funcionalidade absorvida pelo sbrgestao
    "pedidomobile",         # arquivado
}

CLUSTERS = {
    "sbrgestao": "sobral-core", "sbrchecks": "sobral-core", "agnvendas-painelsbr": "sobral-core",
    "pedidomobile": "sobral-core", "sigmed": "sobral-core", "nexus-labsobral": "sobral-core",
    "SBR-ocomon-5.0": "sobral-core", "SbrTask": "sobral-core", "centroculturalsbr": "sobral-core",
    "sicefsus-sistema": "gov-publico", "CertiSYS": "gov-publico",
    "tokentown": "produtos", "hqplus": "produtos",
    "flowdigitalstudio": "produtos", "contabilplus": "produtos", "FinanceFlow": "produtos",
    "mcp-eventos": "mcp-ia", "agnostic-core": "meta-infra",
    "SuperCartolaManagerv5-production": "entretenimento", "bolaocopa2026": "entretenimento",
    "f1-pulse": "entretenimento", "vibegaminghub": "entretenimento",
    "lpjaraujoinfo": "landing-clientes", "temperodemamae": "landing-clientes",
    "AlgodaoAtelie": "landing-clientes", "florianorun": "landing-clientes",
    "lp-restauranteflutuante": "landing-clientes", "lp-ellenpedrosa": "landing-clientes",
    "imersaobitrix24": "landing-clientes", "GessoExpress": "landing-clientes",
    "botclinop": "landing-clientes",
}


def readme_excerpt(full_name, tok):
    try:
        data, _ = api(f"/repos/{full_name}/readme", tok)
        raw = base64.b64decode(data["content"]).decode("utf-8", "ignore")
        lines = [l.strip() for l in raw.splitlines()
                 if l.strip() and not l.lstrip().startswith(("#", "!", "-", "=", "<", "```", "|"))]
        return " · ".join(lines[:5])[:350]
    except Exception:
        return ""


def root_struct(full_name, tok):
    try:
        tree, _ = api(f"/repos/{full_name}/contents/", tok)
        dirs = [i["name"] for i in tree if i["type"] == "dir"]
        files = [i["name"] for i in tree if i["type"] == "file"]
        out = ""
        if dirs:
            out += "dirs : " + ", ".join(dirs) + "\n"
        if files:
            out += "files: " + ", ".join(files)
        return out
    except Exception:
        return ""


def days_idle(pushed_at):
    dt = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


def status_of(days):
    return "ativo" if days <= 30 else "recente" if days <= 90 else "dormant"


def write_ficha(r, tok):
    name = r["name"]
    owner = r["full_name"].split("/")[0]
    days = days_idle(r["pushed_at"])
    cluster = CLUSTERS.get(name, "nao-classificado")
    vis = "privado" if r["private"] else "publico"
    struct = root_struct(r["full_name"], tok)
    excerpt = readme_excerpt(r["full_name"], tok)
    owner_line = f"| owner         | {owner} |\n" if owner != "paulinett1508-dev" else ""
    md = f"""# {name}

| campo         | valor |
|---|---|
| url           | {r['html_url']} |
{owner_line}| visibilidade  | {vis} |
| cluster       | {cluster} |
| status        | **{status_of(days)}** ({days} dias sem commit) |
| linguagem     | {r.get('language') or '-'} |
| tamanho       | {r['size']} KB |
| issues        | {r['open_issues_count']} abertas |
| criado        | {r['created_at'][:10]} |
| ultimo-commit | {r['pushed_at'][:10]} |

## Descrição

{r.get('description') or ''}

## README (excerpt)

{excerpt}

## Estrutura raiz

```
{struct}
```

## Notas do guardião

<!-- observações, alertas, dependências cruzadas -->
"""
    (PLANETS / f"{name}.md").write_text(md, encoding="utf-8")


def rebuild_index(repos):
    icon = {"ativo": "🟢", "recente": "🟡", "dormant": "🔴"}
    rows = []
    for r in sorted(repos, key=lambda x: x["name"].lower()):
        days = days_idle(r["pushed_at"])
        cluster = CLUSTERS.get(r["name"], "nao-classificado")
        lock = "🔒" if r["private"] else ""
        rows.append(f"| {icon[status_of(days)]}{lock} [{r['name']}](planets/{r['name']}.md) "
                    f"| {cluster} | {r.get('language') or '-'} | {r['open_issues_count']} |")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = f"""# theuniverse — Mapa dos Planetas

> Atualizado: {today} | {len(repos)} planetas mapeados (Censo automático)

🟢 ativo (≤30d) · 🟡 recente (31-90d) · 🔴 dormant (>90d) · 🔒 privado

| planeta | cluster | linguagem | issues |
|---|---|---|---|
{chr(10).join(rows)}

---

## Clusters

| cluster | descrição |
|---|---|
| sobral-core | Sistemas do Laboratório Sobral |
| gov-publico | Sistemas governamentais e públicos |
| produtos | Produtos SaaS e plataformas |
| mcp-ia | Servidores MCP e integrações IA |
| meta-infra | Infraestrutura transversal (skills, agentes) |
| landing-clientes | Landing pages e projetos de clientes |
| entretenimento | Projetos pessoais e lúdicos |
"""
    (PLANETS / "_index.md").write_text(body, encoding="utf-8")


def log_changes(novos, explodidos):
    if not (novos or explodidos):
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [f"\n## {today} — Censo automático\n"]
    if novos:
        parts.append("### 🆕 Planetas descobertos")
        parts += [f"- **{n}** — entrou no universo" for n in novos]
    if explodidos:
        parts.append("### 💥 Planetas sumidos")
        parts += [f"- **{e}** — não consta mais no GitHub (ficha arquivada)" for e in explodidos]
    existing = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else "# theuniverse — Diário de Bordo\n\n"
    block = "\n".join(parts) + "\n"
    idx = existing.find("\n## ")  # insere antes da primeira entrada datada
    if idx == -1:
        CHANGELOG.write_text(existing.rstrip() + "\n" + block, encoding="utf-8")
    else:
        CHANGELOG.write_text(existing[:idx] + "\n" + block + existing[idx + 1:], encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tok = token()
    repos = [r for r in list_repos(tok) if r["name"] not in EXCLUDE]
    current = {r["name"] for r in repos}
    fichas = {p.stem for p in PLANETS.glob("*.md") if p.stem not in ("_index", SELF)}

    novos = sorted(current - fichas)
    explodidos = sorted(fichas - current)

    print(f"Censo: {len(repos)} planetas | 🆕 {len(novos)} novos | 💥 {len(explodidos)} sumidos")
    for n in novos:
        print(f"  🆕 {n}")
    for e in explodidos:
        print(f"  💥 {e}")

    if args.dry_run:
        print("(dry-run: nada escrito)")
        return 0

    for r in repos:
        if r["name"] in novos:
            write_ficha(r, tok)
    for e in explodidos:
        (PLANETS / f"{e}.md").unlink(missing_ok=True)

    rebuild_index(repos)
    log_changes(novos, explodidos)
    print("Registro atualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
