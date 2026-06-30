---
tipo: bot
nome: Claude Usage
username: via Obi-Wan (@guardiao_universo_bot)
papel: outbound-notifier
status: ativo
token_secret: TELEGRAM_TOKEN
chat: SOL_CHAT_ID (privado — chat pessoal do TheGod)
script: scripts/weekly-usage-notify.py
workflow: cron local na máquina dev (Task Scheduler Windows)
---

# Claude Usage — Monitor de Uso do Claude Code

Notifica o uso semanal do Claude Code (tokens). Digest a cada 2h entre 05h–23h; alerta de threshold 1x/dia quando o gasto semanal ultrapassa o limite configurado.

Usa o canal do Obi-Wan (`@guardiao_universo_bot`) enviando direto para o chat pessoal do TheGod (`SOL_CHAT_ID`) — sem grupo, sem tópico.

## Cadência

Cron local na máquina dev via Windows Task Scheduler (`Claude-WeeklyUsageNotify`).
Executa: `C:\Users\pmiranda\AppData\Local\Programs\Python\Python313\python.exe`
Script local: `C:\Users\pmiranda\.claude\scripts\weekly-usage-notify.py`

## Config

Lê limite de `~/.claude/weekly-limit.json`:
- `weeklyTokenLimit` — limite semanal em tokens (calibrar via `/usage` no claude.ai)
- `dailyAlertThreshold` — % do limite que dispara alerta (default: 0.10 = 10%/dia)
- `vaultPath` — path do `.vault` com as credenciais

## Mensagens

**Digest (a cada 2h, sempre):**
```
⚡ Claude Code · 09:00

Semana: ████████░░ 80%
Hoje: 3,2% (61,0M)

914,3M / 1,9B · Reseta sex 08h BRT
```

**Alerta (1x/dia, quando hoje > threshold):**
```
🔴 Claude Code — Meta Diária Atingida

⚠️ Você consumiu 12,1% da cota semanal hoje — meta de 10% atingida.

Semana: ██████████ 48% usada
(iniciou hoje em 35,9% · +12,1% no dia)

Hoje: 230,0M · Semana: 914,3M
Limite: 1,9B · Reseta sex 08h BRT
```

## Relacionado

- [[bots/_index]]
- [[planets/theuniverse]]
