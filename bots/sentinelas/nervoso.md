---
tipo: bot
nome: Sistema Nervoso
username: universo_nervoso_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_NERVOSO
telegram_topic: sentinel
script: scripts/sentinel.py
workflow: .github/workflows/sentinel.yml
---

# Sistema Nervoso

Observa todos os repos do universo a cada 15min. Detecta: novos planetas, planetas sumidos, CI com falha, issues novas, segredos expostos. Aciona [[bots/artoo|Artoo]] automaticamente em `ci_falhou`.

## Cadência

`*/15 * * * *` — a cada 15 minutos

## Eventos detectados

| evento | destino |
|---|---|
| `novo_planeta` | Telegram tópico `sentinel` |
| `planeta_sumido` | Telegram tópico `sentinel` |
| `ci_falhou` | Telegram tópico `sentinel` + aciona [[bots/artoo]] |
| `issue_nova` | Telegram tópico `sentinel` |
| `secret_exposto` | Telegram tópico `sentinel` |
| heartbeat | Telegram tópico `sentinel` |

## Estado persistido

`state/sentinel-state.json` (commitado no repo via workflow)

## Relacionado

- [[bots/_index]]
- [[bots/artoo]] — cão de guarda que aciona
- [[planets/sentinel-core]]
