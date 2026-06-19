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

### 2. Hermes-Oráculo (subsistema A) — plano escrito, falta executar
- Spec: `docs/ecossistema/A-hermes-oraculo-spec.md` · Plano: `docs/ecossistema/A-hermes-oraculo-plan.md` (6 tasks TDD, código completo).
- Próximo passo: **executar no repo `nexus-labsobral`** (Guardião não coda fora — abrir sessão lá).
- Antes do deploy (Task 6), credenciais pendentes do Sol: token BotFather, `SOL_CHAT_ID`, modelo Ollama de chat (`ollama list` / `ollama pull qwen2.5`), deploy token de leitura do theuniverse na Polaris. SSH Polaris: `id_ed25519_nexus_vps01`, porta 49222, `root@2.25.163.125`.

### 3. Frota — ✅ FECHADA (2026-06-19)
Rigel = build/CI · Bellatrix = banco · Vega = monitoramento. Registrado em `docs/ecossistema/frota.md`. Frota 100% mapeada.

### 4. Subsistemas futuros (ordem B→C→D)
- **B** — Sistema Nervoso (notificar tudo): eventos dos planetas → bot. Depende de A.
- **C** — Guardião da Galáxia (segurança): curadoria de skills + varredura local + escudos. Dívida registrada: `hermes-dashboard.service` roda inseguro em `0.0.0.0:9119`.
- **D** — Satélites Naturais (motores IA locais por planeta). Nebuloso, precisa brainstorm próprio.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse).
- Satélite orbita **um** planeta — instância isolada. Mas **receita** validada é compartilhada via gravidade.
- Não ler inventários de infra sensíveis (IPs/vault) sem pedido explícito.
- Token vive só no `.vault` (local) e no `.git/config`. Nunca commitar.
