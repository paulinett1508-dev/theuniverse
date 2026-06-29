---
tipo: bot
nome: Deps
username: universo_deps_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_DEPS
telegram_topic: deps
script: scripts/deps.py
workflow: .github/workflows/deps.yml
---

# Deps — CVEs nos Planetas

Varre dependências de todos os repos diariamente, detectando CVEs e vulnerabilidades conhecidas via GitHub Dependabot alerts.

## Cadência

`0 6 * * *` — diário às 06h UTC

## Estado persistido

`state/deps-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
