---
tipo: bot
nome: Escudos
username: universo_escudos_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_ESCUDOS
telegram_topic: escudos
script: scripts/c1-update-github-ips.py
workflow: .github/workflows/c1-update-ips.yml
---

# Escudos — Atualiza IPs do GitHub na Polaris

Toda segunda-feira atualiza as regras UFW da Polaris com os CIDRs atuais do GitHub, garantindo que a porta 9120 (webhooks) aceite apenas tráfego legítimo do GitHub.

## Cadência

`0 4 * * 1` — toda segunda-feira às 04h UTC

## O que faz

1. SSH na Polaris (195.200.5.145)
2. `git pull` do theuniverse em `/opt/theuniverse`
3. Executa `c1-update-github-ips.py` → atualiza UFW
4. Notifica Telegram com resumo das mudanças

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
- [[docs/ecossistema/frota]] — Polaris é a estrela-servidor
