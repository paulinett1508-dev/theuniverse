# Spec — Subsistema B: Sistema Nervoso (notificações sensoriais)

> Status: **design aprovado pelo TheGod** (2026-06-19). Falta: plano de implementação + execução.
> Parte do [Blueprint do Ecossistema](00-blueprint.md). Segundo dos 4 subsistemas (A→B→C→D).
> Depende de **A** ([Hermes-Oráculo](A-hermes-oraculo-spec.md)): reusa o bot do Telegram como trilho de saída.

## Objetivo

Dar ao universo um **sistema nervoso sensorial**: o observatório sente o que já enxerga via API e empurra os eventos de sinal alto pro Telegram do TheGod. Fluxo **outbound** (universo → TheGod), complementar ao A (inbound: TheGod pergunta, Oráculo responde). Os dois dividem o mesmo bot — o *trilho* universal do blueprint.

## Decisões travadas

| decisão | valor |
|---|---|
| Fonte dos eventos | **Só observação via API GitHub** — zero código/instrumentação nos planetas (regra de ouro intacta) |
| Onde roda | **theuniverse** (GitHub Actions cron) — casa do Guardião, estende o Censo. **Desvia** do blueprint (núcleo na Polaris): só a notificação migra; o núcleo pesado (RAG/chat) fica na Polaris |
| Transporte | poll (não webhook) — latência de minutos é irrelevante pra um humano lendo Telegram; webhook exigiria porta exposta (anti-padrão, abre superfície pro subsistema C) |
| Trilho de saída | mesmo bot do A — `sendMessage` da API do Telegram. A escuta (inbound), B fala (outbound) |
| Estado | `state/sentinel-state.json` commitado no theuniverse (auditável; escreve só em casa) |

## Eventos do MVP (sinal alto)

| evento | detecção | estado rastreado |
|---|---|---|
| 🆕 novo planeta | diff lista de repos (API) vs `known_repos` | `known_repos` |
| 💥 planeta sumiu | diff inverso | `known_repos` |
| 🔴 CI/Actions falhou | último run de Actions por repo com `conclusion=failure` | `last_run_id` por repo |
| 🚨 issue nova aberta | `issues?state=open&sort=created` por repo | `last_issue_number` por repo |

**Fora do MVP (ruído):** cada push/commit, stars, forks, PRs rotineiros. Eventos de runtime (deploy concluído, erro em produção) ficam pro subsistema C/futuro — exigem instrumentar planeta via gravidade (opt-in).

## Arquitetura

```
GitHub Actions (cron */15 + workflow_dispatch)
   └─► sentinel.py
        ├─ lê state/sentinel-state.json
        ├─ poll API GitHub (repos, runs, issues)   [UNIVERSE_PAT]
        ├─ calcula deltas vs estado
        ├─ pra cada delta:
        │    └─ Telegram sendMessage(SOL_CHAT_ID)   [TELEGRAM_TOKEN]
        │       └─ só avança o estado daquele evento se o envio deu certo
        └─ commita state/sentinel-state.json (só se mudou)
```

Tudo dentro do theuniverse. Sem servidor, sem porta exposta, sem SSH.

## Componentes

| arquivo | papel |
|---|---|
| `scripts/gh.py` | **refactor**: extrai `token()` / `api()` / `list_repos()` hoje dentro do `censo.py`. Censo e Sentinel importam daqui (DRY) |
| `scripts/sentinel.py` | poll → diff → notifica → commita estado |
| `.github/workflows/sentinel.yml` | cron `*/15 * * * *` + `workflow_dispatch` |
| `state/sentinel-state.json` | estado entre runs: `{known_repos, last_run_id, last_issue_number}` |
| `scripts/censo.py` | **modificar**: passa a importar de `gh.py` (sem mudar comportamento) |

## Comportamentos críticos

- **Primeiro run = baseline silencioso.** Sem `sentinel-state.json`, semeia o estado completo **sem notificar** (senão floda com toda issue aberta marcada como "nova"). Notifica só a partir do 2º run.
- **Entrega antes de avançar.** O estado de um evento só é atualizado após `sendMessage` 200 OK. Falha de Telegram → estado não avança → re-tenta no próximo run. Nada se perde, nada duplica em condição normal.
- **Isolamento de falha.** Erro de API num repo é capturado por repo (try/except) e não derruba o run inteiro.
- **Rate limit.** ~31 repos × poucas chamadas a cada 15 min cabe folgado nos 5000 req/h autenticados.

## Segurança

- `UNIVERSE_PAT`, `TELEGRAM_TOKEN`, `SOL_CHAT_ID` como **secrets do Actions** — nunca no código.
- `UNIVERSE_PAT` é o mesmo do Censo (já pendente de cadastro pelo TheGod).
- Token de leitura apenas; o único `git push` é do estado, no próprio theuniverse.

## Dependência de A

B precisa apenas que o **bot exista** (token do BotFather + `SOL_CHAT_ID` conhecido) — **não** precisa do código do A rodando. Logo B pode ser implementado já e ativado assim que o TheGod gerar os dois tokens (ele confirmou que gera ambos no momento do deploy).

## Credenciais necessárias (TheGod fornece no deploy)

1. **`UNIVERSE_PAT`** — secret no Actions (mesmo token do Censo, do `.vault`).
2. **`TELEGRAM_TOKEN`** — do BotFather (mesmo bot do A). *TheGod gera.*
3. **`SOL_CHAT_ID`** — chat_id do TheGod. *TheGod gera.*

## Fora do MVP (YAGNI)

Webhooks · eventos de runtime/deploy · roteamento por canal/tópico · digest/agrupamento · silenciar horário · histórico persistente além do estado mínimo.

## Self-review

- **Placeholders:** nenhum. Credenciais externas marcadas como "TheGod gera" são fronteira correta, não buraco.
- **Consistência:** estado `{known_repos, last_run_id, last_issue_number}` citado igual na arquitetura, eventos e componentes. `gh.py` é fonte única de `token/api/list_repos` pra Censo e Sentinel.
- **Escopo:** focado num único plano de implementação (1 refactor + 1 script + 1 workflow + 1 estado).
- **Ambiguidade:** "notificar tudo" do blueprint foi explicitamente reduzido a 4 eventos de sinal alto; baseline silencioso resolve o flood do primeiro run.
