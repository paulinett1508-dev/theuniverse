---
tipo: bot
nome: Deploy Health
username: universo_deploy_bot
papel: outbound-notifier
status: ativo
token_secret: TELEGRAM_TOKEN_DEPLOY
telegram_topic: deploy
script: scripts/deploy_health.py
workflow: .github/workflows/deploy-health.yml
---

# Deploy Health — Saúde dos Deploys

Monitora o status dos últimos deploys de todos os repos a cada 30min. Detecta deploys com falha ou regressões.

## Cadência

`*/30 * * * *` — a cada 30 minutos

## Estado persistido

`state/deploy-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
