---
tipo: bot
nome: Farejador
username: universo_farejador_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_FAREJADOR
telegram_topic: seguranca
script: scripts/secret_scan.py
workflow: .github/workflows/secret-audit.yml
---

# Farejador — Varredura de Segredos

Complementa o GitHub secret-scanning nativo com regex de conteúdo customizado. Varre todos os repos diariamente em busca de segredos hardcoded não detectados pelo GitHub.

## Cadência

`30 9 * * *` — diário às 09h30 UTC (~06h30 BRT)

## Estado persistido

`state/secret-scan-state.json` + `state/posture-status.json` (commitados no repo)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
