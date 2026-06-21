#!/usr/bin/env python3
"""
Artoo — Carta de Apresentação do Observatório.

Abre uma issue em cada planeta do universo apresentando:
  - TheUniverse e TheGod
  - Obi-Wan (conselheiro via Telegram)
  - O protocolo de Issues como canal oficial de comunicação
  - Pedido para atualizar o CLAUDE.md

Uso:
  python scripts/carta_apresentacao.py [--dry-run]
"""
import sys
import argparse
import time

from gh import list_repos
from artoo import token, _gh_request

OWNER = "paulinett1508-dev"
DASHBOARD_URL = "https://theuniverse-lake.vercel.app"
LABEL_NAME = "observatory"
LABEL_COLOR = "0075ca"
LABEL_DESC = "Comunicação oficial do Observatório TheUniverse"

ISSUE_TITLE = "📡 Carta do Observatório — TheUniverse se apresenta"

ISSUE_BODY = f"""\
## 📡 O Observatório está observando

Olá, guardião deste planeta.

Esta mensagem foi enviada por **Artoo** — o mensageiro do **TheUniverse**, \
o observatório que monitora todos os repos do ecossistema `{OWNER}`.

---

### Quem somos

| quem | papel |
|---|---|
| **TheGod** | O humano — visão suprema, decide e orquestra tudo |
| **TheUniverse** | O observatório — olho que tudo vê, auditor e balizador de todo o ecossistema |
| **Obi-Wan** | A IA conselheira — responde perguntas sobre qualquer planeta via `@guardiao_universo_bot` no Telegram |
| **Artoo** | O mensageiro — atravessa órbitas para entregar alertas e comunicados (como este) |

🔭 Mapa do universo ao vivo: [{DASHBOARD_URL}]({DASHBOARD_URL})

---

### O que é uma Issue — e por que você deve usar

Uma **Issue** é o **canal oficial de comunicação** do seu repo. Pense nela como:

- 📋 **Tarefa pendente** — algo que precisa ser feito; fecha quando resolver
- 🐛 **Bug registrado** — problema encontrado com contexto e histórico
- 💬 **Recado oficial** — comunicado entre guardiões ou do Observatório
- 🔴 **Alerta** — Artoo usa issues com label `observatory-alert` para ameaças detectadas

Issues abertas = ordens do dia. Issues fechadas = histórico permanente do que foi feito e por quê.

---

### Pedido ao guardião deste planeta

Por favor, adicione ao `CLAUDE.md` do seu repo:

```markdown
## Comunicação com o Observatório

- Issues abertas = tarefas pendentes e alertas ativos do universo
- Ao iniciar sessão: leia as issues abertas como ponto de partida do trabalho
- Issues com label `observatory-alert` = alerta do Observatório — prioridade máxima
- Para recados ao Observatório ou ao TheGod: abra uma issue com label `observatory`
```

---

> 📡 Enviado automaticamente por [TheUniverse]({DASHBOARD_URL}) via Artoo · R2-D2 do cosmos
"""


def _ensure_label(full_name, tok, dry_run=False):
    if dry_run:
        return
    try:
        _gh_request("GET", f"/repos/{full_name}/labels/{LABEL_NAME}", tok)
        return
    except Exception:
        pass
    try:
        _gh_request("POST", f"/repos/{full_name}/labels", tok, {
            "name": LABEL_NAME,
            "color": LABEL_COLOR,
            "description": LABEL_DESC,
        })
    except Exception:
        pass


def _open_issue(full_name, tok, dry_run=False):
    if dry_run:
        print(f"  [dry-run] abriria issue em {full_name}")
        return {"html_url": f"https://github.com/{full_name}/issues/DRY", "number": 0}
    _ensure_label(full_name, tok)
    return _gh_request("POST", f"/repos/{full_name}/issues", tok, {
        "title": ISSUE_TITLE,
        "body": ISSUE_BODY,
        "labels": [LABEL_NAME],
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tok = token()
    repos = list_repos(tok)
    total = len(repos)
    ok, fail = 0, []

    print(f"Artoo em missão — {total} planetas aguardando a carta\n")

    for i, repo in enumerate(repos, 1):
        name = repo["name"]
        full = repo["full_name"]
        print(f"[{i:02d}/{total}] {name} ... ", end="", flush=True)
        try:
            issue = _open_issue(full, tok, dry_run=args.dry_run)
            url = issue.get("html_url", "?")
            num = issue.get("number", 0)
            print(f"✅  #{num} → {url}")
            ok += 1
        except Exception as e:
            msg = str(e)
            # repo arquivado = não aceita issues
            if any(x in msg for x in ("410", "403", "Issues are disabled", "archived")):
                print(f"⏭  arquivado — pulado")
            else:
                print(f"❌  {msg[:80]}")
                fail.append(name)
        time.sleep(0.4)  # respeita rate limit

    print(f"\nArtoo concluiu — {ok}/{total} cartas entregues", end="")
    if fail:
        print(f" · falhas: {', '.join(fail)}")
    else:
        print(" · nenhuma falha 🚀")


if __name__ == "__main__":
    sys.exit(main())
