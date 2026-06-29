---
tipo: bot
nome: Artoo
username: artoo_universo_bot
papel: mensageiro
status: ativo
token_secret: TELEGRAM_TOKEN_ARTOO
telegram_topic: alertas
script: scripts/artoo.py
workflow: acionado por scripts/sentinel.py (ci_falhou)
---

# Artoo — Cão de Guarda / Mensageiro Cósmico

O cão de guarda de [[bots/obi-wan|Obi-Wan]]. Quando o observatório detecta uma ameaça num planeta, Artoo atravessa a órbita e entrega um alerta diretamente no mundo deles via GitHub Issue — o planeta não sabe da ameaça até Artoo chegar.

## Identidade

| campo | valor |
|---|---|
| username | `@artoo_universo_bot` (pendente criação) |
| papel | mensageiro / ação outbound |
| acionado por | [[bots/sentinelas/nervoso]] — evento `ci_falhou` |
| notifica | Telegram tópico `alertas` + GitHub Issue no planeta afetado |

## Personalidade (evolui com missões)

| nível | missões |
|---|---|
| novice | 0–9 |
| journeyman | 10–49 |
| veteran | 50+ |

Estado em: `state/artoo-state.json`

## O que faz

1. Recebe repo + reason + detail do [[bots/sentinelas/nervoso|Sistema Nervoso]]
2. Abre GitHub Issue no planeta afetado com label `observatory-alert`
3. Envia notificação Telegram no tópico `alertas`

## Relacionado

- [[bots/obi-wan]] — quem guarda
- [[bots/sentinelas/nervoso]] — quem aciona
- [[bots/_index]] — todos os bots
- [[planets/sentinel-core]] — repo onde vive
