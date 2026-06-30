# Bots do Universo

> Índice dinâmico (Dataview) + tabela estática de fallback.
> Cast completo: **Obi-Wan** (governante) · **Artoo** (cão de guarda) · **8 sentinelas** (observadores).

## Índice dinâmico (Obsidian + Dataview)

```dataview
TABLE username, papel, status, token_secret, telegram_topic
FROM "bots"
WHERE tipo = "bot"
SORT papel ASC
```

## Tabela estática (fallback GitHub)

| bot | username | papel | status | token_secret | tópico telegram |
|---|---|---|---|---|---|
| [[bots/obi-wan\|Obi-Wan]] | `@guardiao_universo_bot` | conversacional inbound | ativo | `TELEGRAM_TOKEN` | N/A |
| [[bots/artoo\|Artoo]] | `@artoo_universo_bot` | mensageiro / cão de guarda | pendente | `TELEGRAM_TOKEN_ARTOO` | `alertas` |
| [[bots/sentinelas/nervoso\|Sistema Nervoso]] | `@universo_nervoso_bot` | sentinel outbound | pendente | `TELEGRAM_TOKEN_NERVOSO` | `sentinel` |
| [[bots/sentinelas/pulso\|Pulso]] | `@universo_pulso_bot` | uptime outbound | pendente | `TELEGRAM_TOKEN_PULSO` | `pulso` |
| [[bots/sentinelas/deps\|Deps]] | `@universo_deps_bot` | CVEs outbound | pendente | `TELEGRAM_TOKEN_DEPS` | `deps` |
| [[bots/sentinelas/deploy\|Deploy Health]] | `@universo_deploy_bot` | deploy outbound | pendente | `TELEGRAM_TOKEN_DEPLOY` | `deploy` |
| [[bots/sentinelas/farejador\|Farejador]] | `@universo_farejador_bot` | segurança outbound | pendente | `TELEGRAM_TOKEN_FAREJADOR` | `seguranca` |
| [[bots/sentinelas/scout\|Model Scout]] | `@universo_scout_bot` | modelos outbound | pendente | `TELEGRAM_TOKEN_SCOUT` | `model-scout` |
| [[bots/sentinelas/escudos\|Escudos]] | `@universo_escudos_bot` | firewall outbound | pendente | `TELEGRAM_TOKEN_ESCUDOS` | `escudos` |
| [[bots/sentinelas/usage\|Claude Usage]] | via `@guardiao_universo_bot` | uso Claude outbound | ativo | `TELEGRAM_TOKEN` + `SOL_CHAT_ID` | privado (chat TheGod) |

## Relacionado

- [[docs/ecossistema/A-obi-wan-spec]] — spec completo do Obi-Wan
- [[docs/ecossistema/00-blueprint]] — arquitetura do ecossistema
- [[planets/sentinel-core]] — repo onde vivem os bots
