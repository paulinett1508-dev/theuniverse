---
tipo: bot
nome: Model Scout
username: universo_scout_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_SCOUT
telegram_topic: model-scout
script: scripts/model_scout.py
workflow: .github/workflows/model-scout.yml
---

# Model Scout — Radar de Modelos IA

Monitora novos modelos disponíveis na Groq API toda segunda-feira. Notifica quando modelos novos aparecem ou quando modelos usados pelo ecossistema são descontinuados.

## Cadência

`0 8 * * 1` — toda segunda-feira às 08h UTC

## Estado persistido

`state/model-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
- [[planets/hermes]] — usa modelos Groq
