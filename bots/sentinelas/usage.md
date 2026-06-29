---
tipo: bot
nome: Claude Usage
username: universo_usage_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_USAGE
telegram_topic: claude-usage
script: scripts/weekly-usage-notify.py
workflow: N/A (cron local na máquina dev)
---

# Claude Usage — Monitor de Uso do Claude Code

Notifica o uso semanal do Claude Code (tokens/custo). Digest a cada 2h entre 05h–23h; alerta de threshold 1x/dia quando o gasto semanal ultrapassa o limite configurado.

## Cadência

Cron local na máquina dev (não Actions) — configurado via `setup-claude-usage.ps1`.

## Config

Lê limite de `weekly-limit.json` (path configurável por máquina via `.vault`).

## Relacionado

- [[bots/_index]]
- [[planets/theuniverse]]
