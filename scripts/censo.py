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

from gh import API, ROOT, SELF, token, api, list_repos, token_for

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
    "SBR-KPIs": "sobral-core", "gestao-sbr": "sobral-core",
    "serverIA": "mcp-ia", "BI-sobral": "sobral-core", "Projeto-scale": "sobral-core",
    "serverpfsense": "meta-infra",
    "amilcar-cortex": "sobral-core", "amilcar-dominios": "sobral-core", "hermes": "mcp-ia",
    "sicefsus-sistema": "gov-publico", "CertiSYS": "gov-publico", "hospital360": "gov-publico",
    "tokentown": "produtos", "hqplus": "produtos",
    "flowdigitalstudio": "produtos", "contabilplus": "produtos", "FinanceFlow": "produtos",
    "mcp-eventos": "mcp-ia", "agnostic-core": "meta-infra",
    "SuperCartolaManagerv5-production": "entretenimento", "bolaocopa2026": "entretenimento",
    "f1-pulse": "entretenimento", "vibegaminghub": "entretenimento",
    "lpjaraujoinfo": "landing-clientes", "temperodemamae": "landing-clientes",
    "AlgodaoAtelie": "landing-clientes", "florianorun": "landing-clientes",
    "lp-restauranteflutuante": "landing-clientes", "lp-ellenpedrosa": "landing-clientes",
    "imersaobitrix24": "landing-clientes", "GessoExpress": "landing-clientes",
    "luna-base": "observatorio",
    "df-gesso": "produtos",
}

# Cinturões orbitais — natureza gravitacional de cada planeta
# gould:     infra/cortex profissional que também sustenta projetos pessoais (habita dois planos)
# kuiper:    órbita livre do Sol enquanto indivíduo — além do core institucional
# van-allen: campo institucional puro — mais interno, próximo do núcleo Lab Sobral
NATUREZA = {
    # gould — infra/cortex compartilhado
    "agnostic-core": "gould",
    "amilcar-cortex": "gould",
    "amilcar-dominios": "gould",
    "Amilcar-Constellation": "gould",
    "hermes": "gould",
    "luna-base": "gould",
    "mcp-eventos": "gould",
    "sentinel-core": "gould",
    "tokentown": "gould",
    "nexus-labsobral": "gould",
    "sbrgestao": "gould",
    "sbrchecks": "gould",
    # kuiper — órbita pessoal
    "sigmed": "kuiper",
    "hqplus": "kuiper",
    "flowdigitalstudio": "kuiper",
    "contabilplus": "kuiper",
    "CertiSYS": "kuiper",
    "sicefsus-sistema": "kuiper",
    "hospital360": "kuiper",
    "SuperCartolaManagerv5-production": "kuiper",
    "bolaocopa2026": "kuiper",
    "f1-pulse": "kuiper",
    "vibegaminghub": "kuiper",
    "AlgodaoAtelie": "kuiper",
    "florianorun": "kuiper",
    "lp-restauranteflutuante": "kuiper",
    "lp-ellenpedrosa": "kuiper",
    "lpjaraujoinfo": "kuiper",
    "imersaobitrix24": "kuiper",
    "GessoExpress": "kuiper",
    "df-gesso": "kuiper",
    # van-allen — institucional puro (Lab Sobral)
    "centroculturalsbr": "van-allen",
    "FinanceFlow": "van-allen",
    "SBR-KPIs": "van-allen",
    "SbrTask": "van-allen",
    "serverIA": "van-allen",
    "serverpfsense": "van-allen",
    "SBR-ocomon-5.0": "van-allen",
    "gestao-sbr": "van-allen",
    "Projeto-scale": "van-allen",
    "BI-sobral": "van-allen",
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


def write_ficha(r, tok=None):
    name = r["name"]
    owner = r["full_name"].split("/")[0]
    tok = token_for(owner)
    days = days_idle(r["pushed_at"])
    cluster = CLUSTERS.get(name, "nao-classificado")
    natureza = NATUREZA.get(name, "nao-classificado")
    vis = "privado" if r["private"] else "publico"
    struct = root_struct(r["full_name"], tok)
    excerpt = readme_excerpt(r["full_name"], tok)
    owner_line = f"| owner         | {owner} |\n" if owner != "paulinett1508-dev" else ""
    md = f"""# {name}

| campo         | valor |
|---|---|
| url           | {r['html_url']} |
{owner_line}| visibilidade  | {vis} |
| cinturão      | {natureza} |
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
    belt_icon = {"gould": "⚡🏛️", "kuiper": "🌙", "van-allen": "🏛️"}
    for r in sorted(repos, key=lambda x: x["name"].lower()):
        days = days_idle(r["pushed_at"])
        cluster = CLUSTERS.get(r["name"], "nao-classificado")
        natureza = NATUREZA.get(r["name"], "nao-classificado")
        lock = "🔒" if r["private"] else ""
        belt = belt_icon.get(natureza, "❓")
        rows.append(f"| {icon[status_of(days)]}{lock} [{r['name']}](planets/{r['name']}.md) "
                    f"| {belt} {natureza} | {cluster} | {r.get('language') or '-'} | {r['open_issues_count']} |")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = f"""# theuniverse — Mapa dos Planetas

> Atualizado: {today} | {len(repos)} planetas mapeados (Censo automático)

🟢 ativo (≤30d) · 🟡 recente (31-90d) · 🔴 dormant (>90d) · 🔒 privado
⚡🏛️ Gould · 🌙 Kuiper · 🏛️ Van Allen

| planeta | cinturão | cluster | linguagem | issues |
|---|---|---|---|---|
{chr(10).join(rows)}

---

## Cinturões

| cinturão | símbolo | descrição |
|---|---|---|
| Gould     | ⚡🏛️ | Infra/cortex profissional que também sustenta projetos pessoais — habita dois planos |
| Kuiper    | 🌙   | Órbita livre — projetos do Sol enquanto indivíduo, além do core institucional |
| Van Allen | 🏛️   | Campo institucional puro — mais interno, núcleo Lab Sobral |

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
| observatorio | O próprio universo e seus instrumentos |
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
    ap.add_argument("--rebuild-all", action="store_true", help="Reescreve todas as fichas (não só novas)")
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
        if r["name"] in novos or args.rebuild_all:
            write_ficha(r, tok)
    for e in explodidos:
        (PLANETS / f"{e}.md").unlink(missing_ok=True)

    rebuild_index(repos)
    log_changes(novos, explodidos)
    print("Registro atualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
