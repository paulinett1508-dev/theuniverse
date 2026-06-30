---
tipo: bot
nome: Claude Usage
username: via Obi-Wan (@guardiao_universo_bot)
papel: outbound-notifier
status: ativo
token_secret: TELEGRAM_TOKEN
chat: SOL_CHAT_ID (privado — chat pessoal do TheGod)
script: scripts/weekly-usage-notify.py
workflow: Task Scheduler Windows (Claude-Usage-12h00 · 18h00 · 22h00)
---

# Claude Usage — Monitor de Uso do Claude Code

Checkpoint 3x/dia (12h, 18h, 22h BRT) com % semanal real + alerta quando janela 5h > meta diária.

Canal: Obi-Wan (`@guardiao_universo_bot`) → chat privado TheGod (`SOL_CHAT_ID`).

## Arquitetura

```
Claude Code (sessão ativa)
    │
    └─ statusline hook (a cada interação)
         └─ statusline.sh grava ~/.claude/state/rate-limits.json
              └─ {seven_day: {used_percentage: 57}, five_hour: {...}}

Task Scheduler (12h · 18h · 22h BRT)
    └─ weekly-usage-notify.py
         └─ lê rate-limits.json  ← fonte de verdade (Anthropic)
         └─ envia checkpoint via Telegram
```

**Por que não ccusage:** o ccusage lê JSONL locais e subreporta 30–50% do uso real.
O `rate_limits.seven_day` do JSON do statusline vem direto da Anthropic — é o mesmo
número que aparece no `/usage` do Claude Code.

## Fonte de dados

`~/.claude/state/rate-limits.json` — gravado pelo `statusline.sh` a cada interação.
Campos usados:
- `seven_day.used_percentage` — % da cota semanal (fonte de verdade)
- `seven_day.resets_at` — timestamp Unix do próximo reset (sexta 08h BRT)
- `five_hour.used_percentage` — % da janela de 5h atual (proxy do dia)

## Config

`~/.claude/weekly-limit.json`:
- `dailyAlertThreshold` — % da janela 5h que dispara alerta (default: 0.10 = 10%)
- `vaultPath` — path do `.vault`

## Task Scheduler

3 tasks diárias (Python 3.13 global):
```
Claude-Usage-12h00  →  12:00 BRT
Claude-Usage-18h00  →  18:00 BRT
Claude-Usage-22h00  →  22:00 BRT
```
Executor: `C:\Users\pmiranda\AppData\Local\Programs\Python\Python313\python.exe`
Script local: `C:\Users\pmiranda\.claude\scripts\weekly-usage-notify.py`

## Mensagens

**Checkpoint (3x/dia):**
```
⚡ Claude Code · 22h

   └ semana: █████░░░░░ 57%
   └ janela 5h: 7%

Fonte: Claude Code · reseta 03/07 08h BRT
```

**Alerta de meta (1x/dia, quando janela 5h > 10%):**
```
🔴 Claude Code — Meta Diária Atingida

Janela 5h: 12% · meta: 10%
Semana: ██████░░░░ 57%

Reseta sex 08h BRT
```

## Relacionado

- [[bots/_index]]
- [[planets/theuniverse]]
