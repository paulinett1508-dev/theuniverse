# ESTADO DO UNIVERSO — Handoff entre sessões

> **Documento auto-suficiente.** Tudo para retomar o trabalho está aqui — não é preciso colar nada da sessão anterior nem lembrar de nada externo. Este arquivo é injetado automaticamente no contexto a cada sessão (hook SessionStart). Ao lê-lo, você (o guardião) tem o universo inteiro na cabeça.
> Última atualização: 2026-06-19

## ▶️ Primeiro job ao acordar

1. Você é **o Guardião do theuniverse** (papel completo no `CLAUDE.md`). Modo caveman ativo.
2. Pergunte ao Sol qual frente retomar (lista em "🔴 FRENTES ABERTAS" abaixo) — ou siga a que ele indicar.
3. Comandos operacionais prontos:
   - Rodar o Censo manualmente: `python scripts/censo.py` (ou `--dry-run` para só ver)
   - Token GitHub: lido automaticamente do `.vault` pelos scripts.

## Onde está tudo (fonte de verdade = este repo)

| o quê | onde |
|---|---|
| Manifesto do guardião + cosmologia | `CLAUDE.md` |
| Constituição do ecossistema (3 camadas, dois fluxos) | `docs/ecossistema/00-blueprint.md` |
| Frota (servidores = estrelas) | `docs/ecossistema/frota.md` |
| Spec Hermes-Oráculo (subsistema A) | `docs/ecossistema/A-hermes-oraculo-spec.md` |
| Fichas dos planetas | `planets/*.md` + `planets/_index.md` |
| Diário de bordo | `CHANGELOG.md` |
| Censo (auto-descoberta) | `scripts/censo.py` + `.github/workflows/censo.yml` |
| Credenciais (LOCAL, nunca no git) | `.vault` |

## Cosmologia (resumo — detalhe no CLAUDE.md)

☀️ Sol = humano (decide) · 🪐 Planetas = repos · ⭐ Estrelas = servidores · 🛰️ Satélites = motores IA locais · Gravidade = agnostic-core. Guardião = Claude (lê tudo, escreve só em casa).

## ✅ Concluído nesta jornada

- Universo no GitHub: `github.com/paulinett1508-dev/theuniverse` (privado, push via token Classic no `.git/config`)
- agnostic-core instalado como submodule (`.agnostic-core/`)
- 31 planetas mapeados + auto-descoberta funcionando (Censo achou `centroculturalsbr` ao vivo)
- Faxina: `escalaIA` explodido. 4 cascas vazias preservadas (incubação): `botclinop`, `lp-restauranteflutuante`, `lp-ellenpedrosa`, `contabilplus`
- Identidade visual VS Code (azul celeste, title bar preto)
- Blueprint do ecossistema de comunicação (3 camadas, federação não anexação)
- Frota batizada (estrelas)

## 🔴 FRENTES ABERTAS — retomar aqui

### 1. Censo automático — falta 1 passo do Sol
Adicionar secret no GitHub: **Settings → Secrets and variables → Actions → New repository secret**
- Nome: `UNIVERSE_PAT` · Valor: o token do `.vault`
- Sem isso, o cron diário falha auth (mas `workflow_dispatch` manual e uso local via `.vault` funcionam).

### 2. Hermes-Oráculo (subsistema A) — spec v2 aprovado, falta plano + execução
- **Redesenhado** (v2): de RAG-puro Ollama/Qdrant → **receita do SHELDON** (Groq Llama 70B + RAG BM25 + injeção de contexto ao vivo). Plano antigo `A-...-plan.md` está OBSOLETO.
- Spec v2: `docs/ecossistema/A-hermes-oraculo-spec.md`. Código em `theuniverse/oraculo/` (Guardião escreve), runtime systemd long-polling na **Polaris**. Mesmo bot do B (sem conflito: B só sendMessage).
- Responde: "qual repo >30 dias?" (contexto ao vivo via gh.py) + "repo X roda em qual banco?" (RAG sobre fichas). Infra de lab = federa com SHELDON, não remonitora.
- Plano v2: `docs/ecossistema/A-hermes-oraculo-plan-v2.md` (6 tasks TDD, código completo). Tasks 1-5 implementáveis/testáveis EM CASA; Task 6 (deploy) só roda contra a Polaris.
- Próximo passo: **executar** (executing-plans) — igual ao B.
- Credenciais `[PENDENTE SOL]` no deploy: `GROQ_API_KEY` (reusar do SHELDON ou nova), `GITHUB_TOKEN` read-only na Polaris, SSH Polaris (`id_ed25519_nexus_vps01`:49222, root@2.25.163.125). TELEGRAM_TOKEN + SOL_CHAT_ID já conhecidos.

### 3. Frota — ✅ FECHADA (2026-06-19)
Rigel = build/CI · Bellatrix = banco · Vega = monitoramento. Registrado em `docs/ecossistema/frota.md`. Frota 100% mapeada.

### 4. Subsistemas futuros (ordem B→C→D)
- **B** — Sistema Nervoso: ✅ **IMPLEMENTADO** (5/5 tasks, 13 testes passando). `scripts/gh.py` + `scripts/sentinel.py` + `.github/workflows/sentinel.yml`. Censo refatorado pra usar `gh.py` (smoke OK). **Falta só ativar:**
  1. Cadastrar 3 secrets no GitHub Actions: `UNIVERSE_PAT` (=Censo), `TELEGRAM_TOKEN` + `SOL_CHAT_ID` (Sol gera os 2 do bot).
  2. `workflow_dispatch` manual → 1ª run semeia `state/sentinel-state.json` em silêncio (baseline). 2ª run em diante notifica.
  - **PUSH pendente:** commits locais no master ainda não foram pra origin (workflow só roda após push).
- **C** — Guardião da Galáxia (segurança): curadoria de skills + varredura local + escudos. Dívida registrada: `hermes-dashboard.service` roda inseguro em `0.0.0.0:9119`.
- **D** — Satélites Naturais (motores IA locais por planeta). Nebuloso, precisa brainstorm próprio.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse).
- Satélite orbita **um** planeta — instância isolada. Mas **receita** validada é compartilhada via gravidade.
- Não ler inventários de infra sensíveis (IPs/vault) sem pedido explícito.
- Token vive só no `.vault` (local) e no `.git/config`. Nunca commitar.
