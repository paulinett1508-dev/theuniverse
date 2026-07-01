---
tipo: bot
nome: Obi-Wan
username: guardiao_universo_bot
papel: conversacional
status: ativo
token_secret: TELEGRAM_TOKEN
telegram_topic: N/A (inbound — recebe mensagens de TheGod)
script: obi-wan/bot.py
workflow: N/A (systemd na Polaris — long-polling 24/7)
---

# Obi-Wan — Governante Conversacional

O governante do universo. Canal bidirecional entre TheGod e o ecossistema via Telegram. Único bot que **recebe** mensagens — todos os outros só enviam.

## Identidade

| campo | valor |
|---|---|
| username | `@guardiao_universo_bot` |
| papel | conversacional inbound |
| runtime | systemd na Polaris (long-polling) |
| cérebro | Groq GPT-OSS 120B (`openai/gpt-oss-120b`) |
| RAG | BM25 sobre markdowns do theuniverse |
| whitelist | `chat_id = 1030157568` (TheGod only) |

## Missão

TheGod pergunta em linguagem natural; Obi-Wan responde combinando **RAG** (fichas, docs, CLAUDE.md) com **contexto ao vivo** (gh.py + sentinel-state.json). É a fundação da comunicação inteligente — complemento inbound do sistema de sentinelas (outbound).

## Exemplos de perguntas que responde

- *"Qual repo está há mais de 30 dias sem commit?"*
- *"O repo X roda em qual banco de dados?"*
- *"Quantos planetas no cinturão kuiper?"*

## Fora de escopo

- Infra de lab (disco, AD, Samba) → isso é com o SHELDON
- Executar ações em repos → subsistema C (futuro)

## Cão de Guarda

[[bots/artoo|Artoo]] é seu guardião — acionado pelos sentinelas quando detectam ameaça num planeta.

## Spec completo

[[docs/ecossistema/A-obi-wan-spec]]

## Relacionado

- [[planets/sentinel-core]] — repo onde vive
- [[bots/_index]] — todos os bots
- [[bots/artoo]] — cão de guarda
