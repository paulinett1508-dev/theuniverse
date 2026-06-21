# theuniverse — Diário de Bordo

Registro de eventos cósmicos: nascimentos, explosões, fusões e migrações de planetas.



## 2026-06-20 — Dashboard NOC v2.1: canvas especiais por tipo de corpo

### 🎨 Canvas dedicados no card lateral
- `drawStation()` — hexágono metálico giratório com hub central, raios e anel externo. Animação via `rotate: 1turn` (individual transform, sem conflito com hover `scale`).
- `drawSatellite()` — diamante + painéis solares bilaterais com grid + antena beacon pulsante. Caractere `−` corrigido para ASCII (unicode U+2212 causava SyntaxError JS).
- `drawObservatory()` — esfera cinza-azulada com crateras, trilha orbital pontilhada e lua menor em órbita animada.
- `startPlanetAnim()` roteia por bodyType: station → drawStation, satellite → drawSatellite, observatory → drawObservatory, demais → drawPlanet.

### 🌙 luna-base (ex-botclinop)
- Repo renomeado no GitHub via API REST (`PATCH /repos/paulinett1508-dev/botclinop`).
- `planets/luna-base.md` criada, `planets/botclinop.md` removida.
- `SPECIAL_BODIES` e `detect_planet` (Oráculo) atualizados para `luna-base`.

### 🤖 Oráculo v3.2 — sticker + emoji-only fix
- Reply a notificação agora dispara sticker `orbit_confirmed` (🌌) antes de responder.
- Mensagem com só emoji (ex: 🚀) usa query implícita `"status de {repo}"` em vez de mandar o emoji como pergunta ao LLM.

## 2026-06-20 — Dashboard NOC v2: cosmologia planetária

### 🌌 Cinco tipos de corpos celestes
- `SPECIAL_BODIES` em `api/planets.js` — mapa de repos para tipos: station, satellite, observatory, supernova, toys.
- `agnostic-core` → 🛸 Estação Espacial: hexágono fixo entre sol e anel 1, não orbita, gira lento.
- `mcp-eventos` → 🛰 Satélite Artificial: diamante, forçado ao anel 0 (mais interno).
- `luna-base` → 🌙 Observatório Lunar: sphere branco-azulada com anel pontilhado.
- `bolaocopa2026` / `f1-pulse` → 💥 Supernova Iminente: pulso vermelho-laranja.
- `vibegaminghub` → 🎮 Planeta Toys: gradiente rosa↔roxo↔azul animado.

### 🎨 Paleta cromática determinística
- 6 tonalidades por estado de saúde (healthy/warning/alert) via `hashStr(planet.name) % 6`.
- Nenhum planeta visualmente idêntico ao outro.
- Tamanhos aumentados: range 8–26px (era 6–18px).

### 📋 Métricas novas no card
- Linguagem principal com dot colorido (`primaryLanguage.color`).
- Contribuidores (`mentionableUsers.totalCount`).
- Último PR: badge de estado + título + data.
- XSS fix: helper `esc()` + `safeHex()` em todos os campos interpolados em innerHTML.

### ☠️ sbrgestao — Estrela da Morte
- CI `agnvendas-unit-tests failure` detectado — `health: alert` intencional para forçar investigação.
- Não suprimir — Estrela da Morte serve de sinal de alerta para o planeta.

## 2026-06-20 — Dashboard NOC: observatório visual do universo

### 🌌 Orbital map — 27 planetas em órbita animada
- `dashboard/index.html` + `vercel.json` — SPA deployada em `theuniverse-lake.vercel.app`.
- 4 anéis orbitais com velocidades diferentes (paralaxe). Planetas distribuídos por atividade: mais ativos no anel interno.
- Starfield com estrelas piscando + **cometas** lentos com núcleo e cauda gradiente (quente/frio) + **bólidos** rápidos em rajadas de 1-3. Tudo no loop do canvas.
- Sol dourado pulsante no centro.

### 🪐 Magnitude dos planetas
- `api/planets.js`: GraphQL GitHub — `diskUsage` + `history.totalCount`. Score log scale (commits×0.65 + diskKB×0.35), normalizado → magnitude 1–5.
- Tamanho do ponto no mapa: 6–18px por magnitude.
- Tooltip mostra `★★★☆☆` + contagem de commits.

### 🎨 Cores por saúde
- 🟢 `healthy`: push <30d, CI ok → verde neon.
- 🟡 `warning`: push >30d ou issues >3 → amarelo.
- 🔴 `alert` (Estrela da Morte): CI FAILURE → vermelho pulsante.
- ⚫ `dormant`: >120d ou arquivado → cinza escuro.

### 📋 Card lateral ao clicar
- Click no planeta → painel desliza (desktop: lateral 270px; mobile: bottom sheet 58vh).
- Planeta selecionado ganha halo branco e continua orbitando.
- Fechar: botão ✕, ESC ou click fora. Mobile: swipe down.
- **Planeta 3D no card**: canvas com esfera real — tema por saúde (azul-verde, laranja, vermelho vulcânico, cinza morto), bandas de superfície em rotação, highlight especular, sombra terminadora, atmosfera com glow. Anéis para magnitude ≥4 (por hash do nome), renderizados em 2 passes (atrás/frente do globo).

### ⚡ Efeitos visuais em tempo real
- `api/events.js`: Vercel function — GitHub `/users/events`, janela 90s. Retorna `{id, repo, type, ts}`.
- Dashboard poll a cada 8s. Por evento novo:
  - push: flash branco + anel shockwave expansivo
  - PR: pulso laranja + anel de onda
  - issue: pisco âmbar suave
  - create/tag: flash esverdeado
- `seenEvents` Set evita re-disparar.

### 🤖 Totalmente responsivo
- Desktop (>900px): painel lateral 270px.
- Tablet (600-900px): painel lateral 230px.
- Mobile (≤600px): bottom sheet 58vh com drag handle e swipe-down para fechar. Tooltip desabilitado (touch). Stats colapsados.

### 🔭 Favicon inline SVG — sem 404.

## 2026-06-20 — Oráculo v3: fluxo de órbita + digitando

### 🪐 Fluxo de órbita — TheGod pede permissão antes de entrar
- `bot.py`: `detect_planet()` — detecta nome de planeta na mensagem (match direto + parcial por segmento).
- Mensagem solta com planeta detectado → Oráculo propõe: "🌍 Identifico relação com **nexus-labsobral**. Entro na órbita para investigar?"
- `SOVEREIGN_PLANETS` (ex: `the-matrix`) → aviso especial: "tem governança própria. Adentro como observador externo?"
- Confirmações: `sim / s / pode / entra / vai / ok / bora`. Negações: `não / nao / n / cancela / voltar`.
- Reply em notificação → entra na órbita direto (gesto já é o consentimento).
- `_pending[]` guarda pergunta + chunks enquanto aguarda confirmação. Nova pergunta durante pendência cancela o fluxo.

### ⌨️ Indicador "digitando..."
- `_typing()` — chama `sendChatAction` com `action=typing` imediatamente ao receber mensagem, antes de processar.
- `_send()` atualizado para HTML parse_mode (alinhado com webhook/sentinel).

## 2026-06-20 — Oráculo v2: reply contextual, multi-turn, estética Telegram

### 💬 Reply contextual — Oráculo entende a notificação sendo respondida
- `oraculo/bot.py`: `extract_reply_context()` — extrai `reply_to_message.text` do update Telegram.
- `oraculo/brain.py`: `reply_context` injetado antes do bloco RAG. `_parse_notification()` extrai fatos estruturados (repo, branch, horário, commits). Fatos apresentados em `<dados_notificacao>` para o model não reproduzir metadados brutos.
- Regra 4 no system prompt: usa fatos extraídos literalmente. "Q hrs foi?" → lê `horario=` e responde direto.

### 🧠 Histórico multi-turn — Oráculo lembra o contexto da conversa
- `oraculo/bot.py`: `_history = []` em `main()`. `brain_fn` guarda os últimos 5 turnos (10 mensagens) e passa para `brain.answer`.
- `oraculo/brain.py`: `build_messages` aceita `history` — injeta como turnos anteriores antes do user message atual.
- Follow-ups como "e o plano 1?" chegam com contexto do repo anterior no histórico.

### 🎯 ctx_repo — RAG filtrado pelo repo ativo
- `_ctx_repo` em `main()` — atualizado a cada reply_context detectado.
- `brain.py`: quando `ctx_repo` definido e sem reply_context, filtra chunks do RAG por source. Sem chunks do repo → model responde "não tenho informação sobre [repo] no contexto atual".
- Evita que "plano 1" recupere doc do Oráculo em vez do repo da conversa.

### 🎨 Estética Telegram
- Notificações multi-commit: strip de prefixos convencionais (`feat(scope):`, `docs:`, `fix:`). Truncação por palavra (não no meio). Bullets sem indentação.
- Respostas do Oráculo: regra 5 — bullets curtos, máx 3-4 linhas. Respostas negativas = 1 linha sem bullet.
- Regra 1 refinada: não dispara em commits que mencionam Zabbix/disco — só recusa perguntas diretas sobre infra.

## 2026-06-20 — Subsistema C implementado (Escudos + Secrets Scan)

### 🛡️ C1 — Escudos: porta 9120 blindada
- `scripts/c1-update-github-ips.py` — busca os CIDRs oficiais do GitHub em `api.github.com/meta`, limpa regras UFW antigas e recria por CIDR. Localhost também permitido.
- Aplicado na Polaris: 6 CIDRs ativos (`192.30.252.0/22`, `185.199.108.0/22`, `140.82.112.0/20`, `143.55.64.0/20`, `2a0a:a440::/29`, `2606:50c0::/32`) + `127.0.0.1`.
- `.github/workflows/c1-update-ips.yml` — cron toda segunda 04h UTC. Pendente: secret `POLARIS_SSH_KEY` no GitHub para execução autônoma.

### 🔑 C2 — Secrets Scan integrado ao sentinel
- `sentinel.py` agora coleta `secret-scanning/alerts` abertos em cada um dos 27 planetas.
- Novo evento `secret_exposto`: notifica Telegram com número do alerta, tipo do secret e link direto ao painel de segurança do repo.
- Graceful fallback: repos sem secret scanning habilitado são ignorados silenciosamente.

### 🗺️ Subsistema D descartado
- Cada planeta decide sua própria IA se necessitar. Não é responsabilidade do observatório.

## 2026-06-20 — Subsistema B2 no ar (Webhook Notifier)

### ⚡ Notificações em tempo real — push e PRs chegam no Telegram
- `webhook/receiver.py` — FastAPI + HMAC-SHA256, porta 9120 na Polaris. Valida assinatura GitHub antes de processar.
- `scripts/setup-webhooks.py` — registra webhook nos repos via GitHub API. Idempotente (cria ou atualiza).
- 27/27 repos com webhook ativo. Notifica: push (qualquer branch) e pull_request (opened/merged/closed).
- PAT renovado: `theuniverse-master-key` com scopes `repo` + `admin:repo_hook` + `admin:org_hook`.
- Testado ao vivo: push em `botclinop` → notificação chegou no Telegram em tempo real.

### 🗺️ Universo finalizado em 27 planetas
- `Lab-Sobral-Dev` removido de `UNIVERSE_OWNERS` — `SBR-ocomon-5.0` fadado ao arquivamento; `SbrTask` será migrado para `paulinett1508-dev/SbrTask` (censo captura automaticamente).
- `agnvendas-painelsbr` e `pedidomobile` adicionados ao `EXCLUDE` — arquivados, read-only.

### ☀️ Skill Sol criada e testada
- `.agnostic-core/skills/automacao/sol-aquece-planetas.md` — 5 passos idempotentes: agnostic-core + CLAUDE.md + .gitignore + CI + HANDOFF.md.
- Testada em `botclinop` (repo vazio). Bug encontrado e corrigido: token não deve ser embutido na URL do `git submodule add`.

## 2026-06-20 — Censo automático

### 💥 Planetas sumidos
- **agnvendas-painelsbr** — não consta mais no GitHub (ficha arquivada)
- **pedidomobile** — não consta mais no GitHub (ficha arquivada)
## 2026-06-20 — Subsistema A no ar (Hermes-Oráculo, deploy na Polaris)

### 🔮 Oráculo respondendo no Telegram
- Deploy concluído na **Polaris** (`195.200.5.145`, porta 22) — VPS do universo (não confundir com o Oráculo da Matrix `2.25.163.125`).
- Serviço systemd `oraculo.service` ativo, restart automático, 227 chunks BM25 indexados.
- Chave de acesso: `~/.ssh/vscode_key` (cadastrada via extensão Hostinger do VS Code).
- Token GitHub fine-grained read-only (`Contents: read`) — se vazar, só lê o theuniverse.
- Validado ao vivo: Sol perguntou no Telegram, Oráculo respondeu com contexto real da API.
- Universo remapeado nesta sessão: `Lab-Sobral-Dev` incluído, `the-matrix`/`matrix-core` excluídos. 31 planetas.

## 2026-06-20 — Censo automático

### 💥 Planetas sumidos
- **matrix-core** — não consta mais no GitHub (ficha arquivada)
- **the-matrix** — não consta mais no GitHub (ficha arquivada)
## 2026-06-19 — Subsistema A implementado (Hermes-Oráculo, receita SHELDON)

### 🔮 O Oráculo que pensa — código vivo
- Redesenho v2: de RAG-puro (Ollama/Qdrant) → **receita do SHELDON** (Groq Llama 70B + RAG BM25 + injeção de contexto ao vivo). Não reinventou a roda.
- `theuniverse/oraculo/`: `config.py`, `rag.py` (BM25), `context.py` (estado vivo via `gh.py`), `brain.py` (Groq + guardrails), `bot.py` (long-polling, auth gate) + `oraculo.service` + `deploy.sh`.
- Um bot, duas bocas: o `guardiao_universo_bot` serve A (inbound) e B (outbound) — sem conflito de polling.
- Responde "qual repo >30 dias?" (contexto vivo) e "repo X roda em qual banco?" (RAG). Infra de lab → federa com SHELDON.
- 13 testes do oráculo passando (26 no total). Spec + plano v2 em `docs/ecossistema/A-*`. Falta só o deploy na Polaris.

## 2026-06-19 — Subsistema B implementado (Sistema Nervoso)

### 🧠 Sensorial do universo — código vivo
- `scripts/gh.py` — cliente GitHub compartilhado (extraído do `censo.py`, DRY).
- `scripts/sentinel.py` — poll API → detecção de 4 eventos (novo/sumido planeta, CI falhou, issue nova) → Telegram. Entrega-antes-de-avançar, baseline silencioso.
- `.github/workflows/sentinel.yml` — cron `*/15`, commita estado em casa.
- 13 testes passando; Censo refatorado sem quebrar (smoke OK). Spec+plano em `docs/ecossistema/B-*`.
- Falta ativar: 3 secrets no Actions + dispatch inicial. Primeiro subsistema do ecossistema a virar código.

## 2026-06-19 — Frota 100% mapeada

### ⭐ 3 estrelas confirmadas pelo Sol
- **Rigel** (labsobral-214) — a forja: build / CI.
- **Bellatrix** (labsrv05-218) — a guardiã: banco de dados.
- **Vega** (labtools01-150) — a vigia: monitoramento (coexiste com Mira/Zabbix).
- Censo validado em dry-run: 31 planetas, 0 drift, auth local via `.vault` OK.

## 2026-06-19 — Plano do Hermes-Oráculo (subsistema A)

### 📋 Plano de implementação escrito
- `docs/ecossistema/A-hermes-oraculo-plan.md` — 6 tasks TDD, código completo, executável no `nexus-labsobral`.
- Baseado na leitura do código real do `hermes/` (rag_server.py, ingest.py, deploy.sh, systemd) via API.
- Decisões: `rag.py` reusa embed/busca do MCP + chat Ollama; `ingest.py` ganha `--source-dir` repetível (2ª fonte = fichas do theuniverse); `deploy.sh` espelha theuniverse em `/opt/theuniverse`.
- Guardião escreveu o plano (doc, em casa); execução roda no `nexus-labsobral` (regra de ouro: não codar fora).

## 2026-06-19 — Hibernação saudável (handoff entre sessões)

### 💾 Persistência com risco zero de esquecimento
- Criado `ESTADO.md` — handoff auto-suficiente (frentes abertas + ponto de retomada). Não exige colar nada da sessão anterior.
- Hook SessionStart injeta o `ESTADO.md` no contexto automaticamente toda nova sessão.
- `CLAUDE.md` aponta `ESTADO.md` como leitura inicial. Memórias atualizadas (project + user Sol).
- Spec do **Hermes-Oráculo** (subsistema A) materializado em `docs/ecossistema/A-hermes-oraculo-spec.md` (design aprovado, pronto pra plano).

## 2026-06-19 — Censo automático

### 🆕 Planetas descobertos
- **centroculturalsbr** — entrou no universo

## 2026-06-19

### ⭐ A Frota batizada — estrelas do universo
- Taxonomia: **servidor = estrela** (a fornalha que sustenta os planetas em deploy). Registrada em `docs/ecossistema/frota.md` (sem IPs).
- VPS: **Polaris** (Oráculo/Hermes), **Antares** (Zion/prod Sobral), **Sirius** (Hostinger/SCM).
- Aglomerado do Lab: **Atlas** (arquivos), **Mira** (Zabbix), **Rigel**, **Bellatrix**, **Vega** (3 últimas: função a confirmar).
- Fronteira: **Heliopausa** (pfsense). Designações Matrix anteriores (Zion/Oráculo) preservadas como histórico.

## 2026-06-18

### 🛰️ Satélite de ideias — Blueprint do ecossistema de comunicação
- Definida a constituição macro SOL ↔ Universo em 3 camadas (`docs/ecossistema/00-blueprint.md`).
- Princípio fundador: **separar transporte de inteligência** (federação, não anexação — ADR-001 the-matrix).
- Regra de ouro: compartilha-se trilho + protocolo + gravidade; **nunca o motor**. Satélite orbita um planeta só.
- Decomposição em 4 subsistemas (A→B→C→D). Motor Hermes (RAG/MCP na VPS Oráculo) será o núcleo. Próximo ciclo: subsistema A (Hermes-Bot).

### 💥 Explosões (deleções)
- **escalaIA** — esqueleto abandonado (só CLAUDE.md + LICENSE + README, 3KB, parado desde abr/26). Nunca virou código. Decisão do sol: não fazia mais sentido na órbita.

### 🔭 Auditoria de vitalidade
- Primeira faxina do universo. Scan de 31 planetas por: tamanho, arquivos, README, dormência.
- **Preservados** apesar de vazios: `lp-ellenpedrosa`, `lp-restauranteflutuante`, `botclinop`, `contabilplus` — estrelas recém-nascidas, ainda a explorar.
- **Falsos positivos esclarecidos**: `matrix-core` (lib TS consumida por nexus-labsobral) ≠ `the-matrix` (meta-projeto de governança). Não eram duplicatas.

## 2026-06-18 — Gênese
- Universo criado. 31 planetas mapeados, agnostic-core instalado como gravidade central.
