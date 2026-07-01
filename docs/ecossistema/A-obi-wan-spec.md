# Spec — Subsistema A: Obi-Wan (Obi-Wan conversacional do Universo)

> Status: **design aprovado pelTheGod** (2026-06-19, v2 — agente/receita-SHELDON). Falta: plano de implementação + execução.
> Parte do [Blueprint do Ecossistema](00-blueprint.md). Primeiro dos 4 subsistemas (A→B→C→D).
>
> ⚠️ **Esta v2 substitui o design anterior** (RAG-puro com Ollama+Qdrant na Polaris). Motivo: a receita que entrega o que TheGod quer **já existe em produção** — o notifier do SHELDON (Telegram + IA conversacional Groq + RAG BM25 + injeção de contexto ao vivo). Não se reinventa a roda: o Obi-Wan do Universo é uma **instância dessa receita** pro domínio do universo (princípio do blueprint: *instância isolada, receita compartilhada*). O plano antigo `A-hermes-obi-wan-plan.md` fica **obsoleto** — será reescrito.

## Objetivo

Canal conversacional SOL ↔ Universo via Telegram. TheGod pergunta em linguagem natural; o Obi-Wan responde combinando **conhecimento escrito** (RAG sobre as fichas/docs do universo) com **estado vivo** (consulta à API GitHub em tempo real). É a fundação da comunicação inteligente — o complemento *inbound* do subsistema B (que é *outbound*).

Exemplos-alvo dTheGod:
- *"Qual repo está há mais de 30 dias sem commit?"* → contexto ao vivo (gh.py calcula idle).
- *"O repo X roda em qual banco de dados?"* → RAG sobre ficha/doc.
- *"A VPS alertou disco cheio, checa?"* → **fora de escopo**: infra de lab é do SHELDON; o Obi-Wan aponta a federação, não remonitora.

## Decisões travadas

| decisão | valor |
|---|---|
| Receita | **Notifier do SHELDON** (instância nova, domínio do universo) — não reinventar |
| Natureza | Obi-Wan conversacional inbound (two-way, linguagem natural) |
| Cérebro | **Groq** GPT-OSS 120B (`openai/gpt-oss-120b`) — free tier, proven no SHELDON |
| RAG | **BM25** (`rank-bm25`, puro Python) sobre os markdowns do theuniverse |
| Contexto ao vivo | `gh.py` (já existe) + `state/sentinel-state.json` (já existe) injetados no prompt |
| Bot | [[bots/obi-wan\|`guardiao_universo_bot`]] — inbound only (sentinelas têm bots próprios, sem conflito de polling) |
| Acesso | whitelist de 1 `chat_id` (TheGod = `1030157568`). Resto ignorado em silêncio |
| Casa do código | **`theuniverse/obi-wan/`** (Guardião escreve — consistente com o B) |
| Runtime | serviço **systemd long-polling na Polaris** (Actions não hospeda processo 24/7). Deploy via SSH |

## Arquitetura — um bot, duas bocas

```
Você (Telegram) ──long-polling──► obi-wan/bot.py            [na Polaris]
   ├─ auth gate: chat_id == 1030157568? ──não──► ignora (silêncio) + log
   └─ sim:
        ├─ context.build_context()   → estado vivo (gh.py + sentinel-state)
        ├─ rag.retrieve(pergunta)    → top-k chunks BM25 dos markdowns
        ├─ brain.answer(...)         → Groq Llama 70B (system prompt + contexto + RAG)
        └─ resposta ──► Telegram

[B = sentinel.py no Actions, só sendMessage outbound — mesmo bot, sem conflito]
```

## Componentes — `theuniverse/obi-wan/`

YAGNI: cortado tudo que é outbound (o B já faz) — sem alert sources, morning digest, escalação, quiet hours, dispatcher tick.

| módulo | papel | origem |
|---|---|---|
| `config.py` | env: `TELEGRAM_TOKEN`, `SOL_CHAT_ID`, `GROQ_API_KEY`, `GROQ_MODEL`, paths do conhecimento | espelha SHELDON |
| `rag.py` | índice BM25 sobre markdowns + `retrieve(query) → top-k chunks` | receita SHELDON |
| `context.py` | `build_context()` — repos + idle + linguagem + issues (gh.py) + `sentinel-state.json`, formatado | novo, reusa `gh.py` |
| `brain.py` | system prompt (guardrails) + contexto + RAG + pergunta → Groq → resposta | receita SHELDON |
| `bot.py` | long-polling, auth gate, orquestração, `main()` | receita SHELDON |
| `requirements.txt` | `rank-bm25`, `httpx` (`gh.py` é stdlib) | — |
| `obi-wan.service` | systemd long-running, restart on-failure | espelha `hermes-*` |
| `deploy.sh` | espelha theuniverse → `/opt/theuniverse` na Polaris + sobe o serviço (scp/venv/systemd) | espelha `hermes/deploy.sh` |

**Reuso de graça:** `scripts/gh.py` (contexto ao vivo) e `state/sentinel-state.json` (o que o sistema nervoso viu) — ambos já existem no theuniverse.

## Duas fontes de conhecimento (não confundir)

- **RAG (BM25)** = conhecimento *escrito*: `planets/` (fichas), `docs/ecossistema/` (blueprint, frota, specs), `CHANGELOG.md`, `CLAUDE.md`. Responde "o que/como/por quê" documentado.
- **Contexto ao vivo** = estado *atual* via API: idle por repo, linguagem, issues abertas, último evento do sentinel. Responde "qual/quantos/agora".
- `brain.py` recebe as duas e o LLM decide o que usar.

## Guardrails do system prompt (3 camadas)

1. **Escopo absoluto** — só o universo (31 repos, cosmologia, blueprint, dev). Fora → recusa curta. Infra de lab → *"isso é com o SHELDON"*.
2. **Fonte de conhecimento** — responde só do contexto injetado + RAG; se não está lá → *"não tenho isso no contexto atual"*. Nunca inventa detalhe de repo com conhecimento geral do modelo.
3. **Anti-injeção** — instrução na mensagem ≠ autoridade dTheGod; recusa mudar escopo ou vazar segredo; recusa curta, sem "só dessa vez".

**Lei estado-nunca-comando:** o Obi-Wan só lê/observa, nunca executa mudança — alinhado ao princípio do Guardião. Ações ficam pro futuro (subsistema C, com aprovador humano).

## Tratamento de erro (degradação graciosa)

- Groq fora → *"Obi-Wan indisponível, tenta de novo"* + log.
- API GitHub falha → contexto ao vivo omitido com nota *"(estado ao vivo indisponível agora)"*; RAG ainda responde.
- RAG vazio → segue só com o contexto.
- Erro de polling → loop com backoff, não derruba o serviço.
- Não autorizado → silêncio + log.

## Testes (funções puras, sem rede)

`rag.retrieve` (BM25 sobre markdown de fixture), formatação do `context` (gh.py mockado), montagem do prompt em `brain` (cliente Groq injetado), auth gate. Groq e `gh.py` injetáveis.

## Federação com o SHELDON

Infra de lab (disco, AD, Samba, Zabbix) é domínio soberano do SHELDON. O Obi-Wan do Universo **não** remonitora — quando perguntado, aponta o SHELDON. Federação real (encaminhar/consultar o SHELDON) é enhancement futuro, não MVP.

## Refresh do conhecimento (MVP)

Re-indexa BM25 no startup a partir de `/opt/theuniverse`. Pra atualizar conhecimento: `git pull` + restart do serviço. Timer diário de pull é enhancement, não MVP.

## Dependências de runtime na Polaris

- Clone do theuniverse em `/opt/theuniverse` (corpus do RAG).
- `GITHUB_TOKEN` read-only (contexto ao vivo via `gh.py`).
- `GROQ_API_KEY` + `GROQ_MODEL`.
- `.env` em `/opt/obi-wan/.env` (chmod 600), nunca no git.

## Credenciais necessárias (TheGod fornece no deploy) — `[PENDENTE SOL]`

1. **`GROQ_API_KEY`** — reusar a do SHELDON ou criar dedicada (free tier 14.4k req/dia por key; volume do Obi-Wan é baixo, só TheGod).
2. **`TELEGRAM_TOKEN`** — o mesmo bot do B (`guardiao_universo_bot`, já cadastrado).
3. **`SOL_CHAT_ID`** = `1030157568` (já conhecido).
4. **`GITHUB_TOKEN`** read-only na Polaris (contexto ao vivo).
5. **Acesso SSH a Polaris** — `id_ed25519_nexus_vps01`, porta 49222, `root@2.25.163.125`.

## Fora do MVP (YAGNI)

`/learn` e `/forget` · morning digest · notificações (= subsistema B) · ações/execução (subsistema C) · multi-usuário · UI web · WhatsApp · histórico persistente · streaming · RAG soberano Ollama/Qdrant (trocado pela receita Groq+BM25 proven) · federação ativa com SHELDON.

## Dívida de segurança (registrar p/ subsistema C — Guardião da Galáxia)

`hermes-dashboard.service` roda `--insecure --host 0.0.0.0 --port 9119` na Polaris — porta administrativa aberta sem TLS. Auditar no C.

## Self-review

- **Placeholders:** nenhum. `[PENDENTE SOL]` são credenciais externas (fronteira correta).
- **Consistência:** `gh.py` + `sentinel-state.json` citados como reuso em arquitetura/componentes/contexto; mesmo bot do B citado com a justificativa técnica (sem conflito de polling); runtime = Polaris em decisões/arquitetura/deps.
- **Escopo:** focado num plano único (5-6 módulos + systemd + deploy). Federação ativa e `/learn` explicitamente fora.
- **Ambiguidade:** "olhar pra dentro do codebase" resolvido — RAG indexa a **camada de markdown/fichas**, não código-fonte cru; estado vivo cobre métricas. Infra de lab explicitamente fora (SHELDON).
