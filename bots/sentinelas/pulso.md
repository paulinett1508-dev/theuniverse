---
tipo: bot
nome: Pulso
username: universo_pulso_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_PULSO
telegram_topic: pulso
script: scripts/pulso.py
workflow: .github/workflows/pulso.yml
---

# Pulso — Uptime dos Planetas

Monitora o status de uptime de todos os planetas com URL pública a cada 15min. Notifica mudanças de estado (up→down, down→up).

## Cadência

`*/15 * * * *` — a cada 15 minutos

## Estado persistido

`state/pulso-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
