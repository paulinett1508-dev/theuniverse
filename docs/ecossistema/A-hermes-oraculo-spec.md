# Spec — Subsistema A: Hermes-Oráculo (bot Telegram conversacional)

> Status: **design aprovado pelo Sol** (2026-06-19). Falta: plano de implementação + execução.
> Parte do [Blueprint do Ecossistema](00-blueprint.md). Primeiro dos 4 subsistemas (A→B→C→D).

## Objetivo

Canal conversacional SOL ↔ Universo via Telegram. O Sol pergunta em linguagem natural; o Oráculo responde consultando o motor Hermes (RAG local na estrela **Polaris**). É a fundação da comunicação — tudo o mais (notificações, Guardião) depende dele.

## Decisões travadas

| decisão | valor |
|---|---|
| Natureza | **Oráculo conversacional** (two-way, linguagem natural) |
| Acesso | **Só o Sol** — allowlist de 1 `chat_id`. Resto ignorado em silêncio |
| Conhecimento | **Universo (fichas) + Lab** — ingere `theuniverse/planets/` + `docs/ecossistema/` + `CHANGELOG.md` além do `lab_knowledge` atual |
| Casa do código | `nexus-labsobral/hermes/bot/` (o bot é parte do motor) |
| Estrela hospedeira | **Polaris** (Oráculo / nexus-vps01, `2.25.163.125`) |

## Arquitetura

```
Sol (Telegram) ──long-polling──► bot.py
   ├─ guard: chat_id == SOL? ──não──► ignora (silêncio)
   └─ sim ► embed(pergunta)  [Ollama nomic-embed-text]
            ► Qdrant search   [coleção lab_knowledge, top-5, score≥0.75]
            ► monta prompt    [contexto recuperado + pergunta]
            ► Ollama chat      [LLM local generativo — modelo a confirmar na VPS]
            ► resposta + fontes ──► Telegram
```
Tudo dentro de Polaris. Long-polling = nenhuma porta nova exposta. Conhecimento soberano (Ollama+Qdrant locais, zero vazamento externo).

## Componentes — `nexus-labsobral/hermes/bot/`

| arquivo | papel |
|---|---|
| `bot.py` | loop Telegram (long-polling), guard de chat_id, orquestração |
| `rag.py` | cliente RAG (embed → search Qdrant → chat Ollama), reusa lógica do `rag_server.py` |
| `config.py` | env: `TELEGRAM_TOKEN`, `SOL_CHAT_ID`, `OLLAMA_URL`, `QDRANT_URL`, `CHAT_MODEL` |
| `requirements.txt` | python-telegram-bot, qdrant-client, requests |
| systemd `hermes-bot.service` | long-running, restart on-failure |

## Conhecimento (Universo + Lab)

- `theuniverse` espelhado para `/opt/theuniverse` na Polaris.
- Ingestor existente (`ingest.py`) ganha 2ª fonte: indexa `planets/` + `docs/ecossistema/` + `CHANGELOG.md`.
- Roda no timer diário das 3h já existente.

## Segurança

- Guard de 1 `chat_id` antes de qualquer processamento.
- `TELEGRAM_TOKEN` em `/opt/hermes-bot/.env` (chmod 600), **nunca no git**.
- Sem webhook → sem porta exposta.

## Deploy

- Estende o `hermes/deploy.sh` existente com bloco do `hermes-bot` (scp → venv → systemd enable).

## Fase pós-validação — extração da receita

Validado no nexus, o padrão "satélite-oráculo" sobe à **gravidade** (agnostic-core) como skill/template replicável. Outro planeta ganha *seu* oráculo (instância isolada, nas suas proporções). Mesmo padrão, motores diferentes. (Ver blueprint: "instância isolada, ideia compartilhada".)

## Fora do MVP (YAGNI)

Notificações push (= subsistema B) · comandos slash · multi-usuário · histórico persistente · streaming.

## Credenciais necessárias (fase de deploy — Sol fornece)

1. **Token do BotFather** (criar o bot no Telegram) → vault, nunca no git
2. **chat_id do Sol** (descobre via `/start` no primeiro boot, ou Sol passa)
3. **Acesso SSH a Polaris** — chave `id_ed25519_nexus_vps01` (confirmar se existe nesta máquina)
4. **Modelo Ollama de chat** instalado na VPS (se nenhum, instalar `qwen2.5` ou `llama3.1`)

## Dívida de segurança registrada (para o Guardião da Galáxia / subsistema C)

`hermes-dashboard.service` roda `--insecure --host 0.0.0.0 --port 9119` — porta administrativa aberta e sem TLS na Polaris. Auditar.
