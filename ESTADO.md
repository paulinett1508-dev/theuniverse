# ESTADO DO UNIVERSO — Handoff entre sessões

> **Documento auto-suficiente.** Tudo para retomar o trabalho está aqui — não é preciso colar nada da sessão anterior nem lembrar de nada externo. Este arquivo é injetado automaticamente no contexto a cada sessão (hook SessionStart). Ao lê-lo, você (o guardião) tem o universo inteiro na cabeça.
> Última atualização: 2026-06-28 (Lab-Sobral-Dev incorporado · Cinturões orbitais · 40 planetas)

## ▶️ Primeiro job ao acordar

1. Você é **o Guardião do theuniverse** (papel completo no `CLAUDE.md`). Modo caveman ativo.
2. Pergunte ao TheGod qual frente retomar (lista em "🔴 FRENTES ABERTAS" abaixo) — ou siga a que ele indicar.
3. Comandos operacionais prontos:
   - Rodar o Censo manualmente: `python scripts/censo.py` (ou `--dry-run` para só ver)
   - Token GitHub: lido automaticamente do `.vault` pelos scripts.

## Onde está tudo (fonte de verdade = este repo)

| o quê | onde |
|---|---|
| Manifesto do guardião + cosmologia | `CLAUDE.md` |
| Constituição do ecossistema (3 camadas, dois fluxos) | `docs/ecossistema/00-blueprint.md` |
| Frota (servidores = estrelas) | `docs/ecossistema/frota.md` |
| Spec Obi-Wan (subsistema A) | `docs/ecossistema/A-obi-wan-spec.md` |
| Spec Webhook Notifier (subsistema B2) | `docs/ecossistema/B2-webhook-notifier-spec.md` |
| Sentinel · Escudos (C1) | `scripts/c1-update-github-ips.py` |
| Manifestos das constelações | `constellations/*.md` |
| Fichas dos planetas | `planets/*.md` + `planets/_index.md` |
| Diário de bordo | `CHANGELOG.md` |
| Censo (auto-descoberta) | `scripts/censo.py` + `.github/workflows/censo.yml` |
| Setup de webhooks | `scripts/setup-webhooks.py` |
| Credenciais (LOCAL, nunca no git) | `.vault` |

## Cosmologia (resumo — detalhe no CLAUDE.md)

O theuniverse é um **observatório pessoal** — olho omnisciente sobre TODOS os repos da conta `paulinett1508-dev`. Observa, diagnostica, organiza. Nunca executa em outros repos.

**Constelação Amilcar** — agrupamento do cortex do Lab Sobral (nexus-labsobral, sbrgestao, sigmed, centroculturalsbr, sbrchecks). Alma de Trantor: governa sem executar. Manifesto em `constellations/amilcar.md`. O repo `the-matrix` está em transição para refletir essa identidade.

Gravidade = agnostic-core (submodule).

## Universo observável (2026-06-23)

**27+ planetas** — todos de `paulinett1508-dev`.

**Excluídos do universo (decisão do TheGod):**
- `the-matrix` — em transição para manifesto da constelação Amilcar (ajustes internos por lá)
- `matrix-core` — mundo Matrix separado
- `baileys-whatsapp-server`, `bitrix-buddy-chat` — repos de terceiros (`rvsigor`)
- `agnvendas-painelsbr`, `pedidomobile` — arquivados (na zona de decadência do BH)
- `Lab-Sobral-Dev/*` — org fora de escopo

**⚠️ Planeta novo detectado pelo censo:** `mybots-telegram` — não indexado ainda (ver issue #9)

**Issues abertas a monitorar:** `agnostic-core`×3 · `tokentown`×1 · `GessoExpress`×1
**CI com falha:** `sbrgestao` — `agnvendas-unit-tests failure` (Estrela da Morte ativa no dashboard)
**Supernovas iminentes:** `bolaocopa2026` · `f1-pulse` — arquivar/excluir quando TheGod decidir

## ✅ Concluído nesta jornada

### Sessão 2026-06-28

**Lab-Sobral-Dev incorporado como Amilcar Prime:**
- `gh.py`: `UNIVERSE_OWNERS` expandido para 2 contas · `all_tokens()` · `token_for(owner)` · `list_repos` varre ambas com token correto
- `.vault`: `GITHUB_TOKEN_LAB` + `GITHUB_USER_LAB` adicionados (Fine-grained PAT, 17 permissões)
- Censo: 40 planetas (era 29) · 11 novos · 8 de Lab-Sobral-Dev + 3 recentes de paulinett1508-dev (amilcar-cortex, amilcar-dominios, hermes)
- `constellations/amilcar.md`: Amilcar Prime (Lab-Sobral-Dev) + Amilcar Secundária documentadas

**Cinturões orbitais (nova dimensão do universo):**
- 3 cinturões: ⚡ compartilhado (12) · 🌙 pessoal (18) · 🏛️ profissional (10)
- `censo.py`: dict `NATUREZA` · campo `cinturão` nas fichas · coluna no `_index.md` · flag `--rebuild-all`
- Todas as 40 fichas regravadas com `cinturão` definido

**Issues:**
- #9 `mybots-telegram` — já estava fechada
- #17 aberta: investigar divergência SbrTask (Lab-Sobral-Dev vs paulinett1508-dev)

**Correção crítica — Telegram tópicos silenciosos:**
- Diagnóstico: 4 de 5 workflows em failure, `secret-audit` único passando
- **Bug 1 — sentinel.yml**: `state/artoo-state.json` untracked ativava o `if` mas `git add state/sentinel-state.json` não o incluía → commit vazio → exit 1. Fix: `git add state/` + `git diff --cached --quiet` antes de commitar
- **Bug 2 — pulso/deps/deploy-health**: usavam `secrets.SENTINEL_GITHUB_TOKEN` (secret inexistente). Python falhava antes de enviar qualquer mensagem. Fix: trocado por `secrets.UNIVERSE_PAT`
- Resultado esperado: tópicos Pulso(8) · Deps(10) · Deploy(12) · Heartbeat(16) voltam a receber mensagens nos próximos crons

**serverIA (Lab-Sobral-Dev) — stack RAG em produção:**
- Ollama (CPU-only) + FastAPI + ChromaDB + Nginx + Scheduler
- `samba_client.py` sugere ingestão de documentos via share de rede (Atlas/Antares)
- Hermes (repo criado 2026-06-26, vazio) é a **evolução planejada** do serverIA — não está deployado ainda

**Pendente desta sessão:**
- Dashboard sentinel-core: visualizar cinturões (nova frente — aguarda decisão de design)
- Webhook setup para os 11 novos planetas (`python scripts/setup-webhooks.py`)
- Validar que os tópicos Telegram voltaram a funcionar após próximo cron
- Definir se Hermes substitui ou expande o serverIA (decisão de arquitetura)

### Sessão 2026-06-24 — parte 2

**Grupo Telegram TheUniverse — tópicos por sentinela:**
- Grupo criado: `TheUniverse` · chat_id `-1004472865546` · supergrupo com forum ativo
- 8 tópicos mapeados: Planetas(2) · Alertas(4) · CI(6) · Pulso(8) · Deps(10) · Deploy(12) · Segurança(14) · Heartbeat(16)
- `send_telegram(text, thread_id=None)` — assinatura atualizada em `sentinel.py`
- Todos os scripts roteiam para o tópico certo: sentinel, artoo, secret_scan, pulso, deps, deploy_health
- `SOL_CHAT_ID` e `TELEGRAM_TOKEN` adicionados ao `.vault` local
- ✅ webhook notifier B2 no Polaris atualizado: `/opt/obi-wan/.env` com novo `SOL_CHAT_ID` e `message_thread_id=2` (Planetas)

**Três novos sentinelas implementados (TDD, 30 testes):**
- Sentinel · Pulso — uptime via `homepage` da API GitHub · cron 15min
- Sentinel · Deps — CVEs via OSV.dev · cron diário 06h
- Sentinel · Deploy — GitHub Deployments API · cron 30min

**Issues abertas:**
- #11 `proxima-sessao` — repos com personalidade cosmológica (estrela jovem, anã branca, Estrela da Morte)
- #12 `proxima-sessao` — Artoo com voz própria aprofundada
- #13 `trigger-based` — James Webb como segundo observatório · plano B revisão 04/07/2026

**Memória salva:** `reference_public_apis.md` — 24 APIs avaliadas, fit por repo, decisão de não usar pop culture como persona

### Sessão 2026-06-24 — parte 1

**Sentinel — Heartbeat do ciclo:**
- `build_heartbeat_report()` + `send_heartbeat()` implementados via TDD (4 testes novos)
- Corrigidos 5 testes regressivos da outra sessão (`_snapshot` sem `secrets`, `"Issue"` → `"🚨"`)
- `main()` acumula `scanned_repos` + `detected_events` e dispara heartbeat ao final de cada ciclo
- Relatório HTML chega no Telegram a cada 15 min: repos escaneados, eventos detectados, ✅/⚠️

**Sentinel · Escudos — observabilidade:**
- Adicionado step de notificação Telegram no workflow `c1-update-ips.yml`
- Corrigida injeção GitHub Actions (`summary` via env var, não interpolado no heredoc Python)

**Renaming C1/C2 → Sentinel · Escudos / Sentinel · Farejador:**
- Atualizado em: `ESTADO.md`, workflows, docstrings dos scripts

**Dashboard v7 — radar de postura no sentinel-core:**
- `api/posture.js` — novo endpoint Vercel que lê `state/posture-status.json`
- Anel radar girante no sentinel-core: cor = `status` da postura (verde/amarelo/vermelho)
- Pulso de 1.5s ao detectar mudança de estado entre polls

**Dashboard v7 — busca com autocomplete:**
- Prefix completion inline: digitar "flori" preenche `florianorun` com seleção no restante
- Navegação por teclado: ↑↓ percorre dropdown, Enter seleciona, Esc fecha, Tab confirma
- Match destacado em amarelo no dropdown, resultados rankeados (prefix primeiro)
- sentinel-core adicionado ao pool de busca (antes só acessível pela legenda)

### Sessão 2026-06-23

**Federação M2M (issue #1 — FECHADA):**
- `obi-wan/api.py` — FastAPI `/ask` porta 9121, Bearer auth (hmac.compare_digest), rate limit por IP
- `obi-wan/api.service` — systemd unit
- `obi-wan/deploy.sh` — atualizado para subir `api.service`
- Deploy na Polaris: `systemctl enable --now api.service` quando `.env` tiver `API_TOKEN`

**Dashboard galáctica v6 (6 correções — commit `af3ad7c`):**
1. **Tilt orbital**: `(ri/20)*0.38` → `(ri/20)*0.06` — florianorun, temperodemamae, lpjaraujoinfo deixam de cruzar as órbitas
2. **Obi-Wan glows**: 0.45/0.18/0.06 → 0.20/0.08/0.025 + PointLight 0.8→0.4
3. **Toggle de luzes**: botão "luzes: on/off" no card Obi-Wan → `_toggleObiWanLights()`
4. **sentinel-core**: removido do `actualMeshes` (era tratado como planeta); wander corrigido: `isPlanet` → `bodyType==='planet'` — Obi-Wan agora realmente visita planetas no modo errante
5. **Zona de decadência (BH)**: todos os objetos agora em `actualMeshes` com hitboxes → hover tooltip + card panel funcionam

**Histórico de sessões anteriores:**
- Sessões 2026-06-19–21: Frota mapeada · Obi-Wan v3.2 · B2/C1/C2 no ar · Dashboard v1-v5 · Artoo · Carta de Apresentação

## 🔴 FRENTES ABERTAS — retomar aqui

### 1. Obi-Wan (subsistema A) — ✅ NO AR | v3.2 + endpoint /ask

Deploy: Polaris `195.200.5.145`. Telegram: `@guardiao_universo_bot`. 227 chunks indexados.

**Infra da Polaris:**
- SSH: `ssh -i ~/.ssh/vscode_key root@195.200.5.145`
- Obi-Wan bot: `systemctl status obi-wan` · `journalctl -u obi-wan -f`
- API /ask: `systemctl status api` · porta 9121 · `journalctl -u obi-wan-api -f`
- Webhook: `systemctl status webhook` · `journalctl -u webhook -f`
- Clone: `/opt/theuniverse` · env: `/opt/obi-wan/.env`
- Atualizar: `git pull` em `/opt/theuniverse` + `systemctl restart obi-wan webhook api`

**Re-deploy do zero:** `bash obi-wan/deploy.sh` + `bash webhook/deploy.sh`

⚠️ `api.service` só inicia se `/opt/obi-wan/.env` tiver `API_TOKEN`. Se ausente, adicionar e `systemctl enable --now api`.

### 2. Subsistema B2 (Webhook Notifier) — ✅ NO AR

27 repos monitorados. Notifica push e PRs em tempo real via Telegram.
Para adicionar novo repo ao universo: `python scripts/setup-webhooks.py` após criar o repo.

### 3. Subsistema C — ✅ IMPLEMENTADO

- **Sentinel · Escudos:** UFW porta 9120 restrita aos CIDRs do GitHub. Cron semanal em `.github/workflows/c1-update-ips.yml`. Notifica Telegram após cada run.
- **Sentinel · Farejador:** varredura de conteúdo por regex em todos os planetas, notifica Telegram e atualiza `state/posture-status.json`.
- **Sentinel · Pulso:** uptime das URLs de produção (`homepage` da API GitHub). Cron 15min. Estado em `state/pulso-state.json`. Notifica queda/retorno + heartbeat.
- **Sentinel · Deps:** CVE scan de `package.json`+`requirements.txt` via OSV.dev API. Cron diário 06h. Estado em `state/deps-state.json`. Notifica novas vulns + heartbeat.
- **Sentinel · Deploy:** saúde de deployments de produção via GitHub Deployments API (Vercel-compatível). Cron 30min. Estado em `state/deploy-state.json`. Detecta regressões + recuperações + heartbeat.

### 4. Dashboard NOC — ✅ NO AR | v7

URL: `theuniverse-lake.vercel.app` (Vercel, deploy automático no push).
Infra: `api/planets.js` + `api/events.js` + `api/posture.js` (Vercel functions). Env var: `GITHUB_TOKEN` no painel Vercel.

**Corpos celestes especiais** (hardcoded em `api/planets.js → SPECIAL_BODIES`):
- station: `agnostic-core` · satellite: `mcp-eventos` · observatory: `luna-base`
- supernova: `bolaocopa2026`, `f1-pulse` · nebula: `vibegaminghub`

**Vista galáctica v7** (`dashboard/index.html`):
- 24 anéis orbitais, ring 0 = orbit 20u, ring 23 = orbit 375u
- Obi-Wan ISS: exílio `(80,120,60)`, wander autônomo quando idle (visita planetas por `bodyType==='planet'`)
- sentinel-core: satélite que orbita a ISS — anel radar girante com cor de postura (🟢 limpo · 🟡 avisos · 🔴 crítico), poll `/api/posture` a cada 60s, pulsa ao detectar mudança
- Zona de decadência (BH): todos os corpos com hitbox no raycaster (tooltip + card)
- Toggle de luzes da ISS: abrir painel Obi-Wan → botão "luzes: on/off"
- **Busca com autocomplete**: prefix completion inline (Tab confirma), ↑↓/Enter/Esc, match destacado em amarelo, sentinel-core incluído no pool de busca

**Novos planetas a adicionar ao mapa forçado:** `mybots-telegram` (ver issue #9)

### 5. Artoo — ✅ IMPLEMENTADO

`scripts/artoo.py` — abre Issues de alerta em planetas + notifica Telegram.
`scripts/carta_apresentacao.py` — enviada a 29/31 planetas.

### 6. Webhooks — ⏳ 11 novos planetas sem webhook

Após incorporação do Lab-Sobral-Dev, 11 planetas novos sem webhook registrado.
Rodar: `python scripts/setup-webhooks.py`

### 7. Dashboard — ⏳ CINTURÕES NÃO VISUALIZADOS

Dado existe (`cinturão` em todas as fichas e na API). Falta representar visualmente no dashboard sentinel-core.
Próxima sessão: planejar layout dos 3 cinturões orbitais.

### 8. SbrTask sync — ⏳ DIVERGÊNCIA (issue #17)

Desenvolvimento migrou de Lab-Sobral-Dev para paulinett1508-dev. Investigar e consolidar.

### 9. sbrgestao CI — ⏳ ESTRELA DA MORTE (issue #10)

`agnvendas-unit-tests failure` — CI vermelho. Dashboard mostra alerta. Investigar antes de próxima sessão de produção.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse). Exceção explícita: **Artoo** (autorizado pelo TheGod) pode abrir Issues de alerta em planetas afetados.
- Constelação Amilcar (`the-matrix` em transição) = ecossistema do Lab Sobral. Manifesto canônico em `constellations/amilcar.md`.
- Token vive só no `.vault` (local) e no `/opt/obi-wan/.env` (Polaris). Nunca commitar. Dois tokens agora: `GITHUB_TOKEN` (paulinett1508-dev) + `GITHUB_TOKEN_LAB` (Lab-Sobral-Dev).
- `UNIVERSE_OWNERS` em `gh.py` é o controle de escopo — alterar só com decisão do TheGod.
- Após adicionar repo ao universo: rodar `python scripts/setup-webhooks.py` para registrar webhook.
- **Issue resolvida = comentar evidência (linhas de código) + fechar com `completed` imediatamente.**

## 💻 Setup em novo computador (arquivos local-only, NÃO versionados)

Ao clonar o theuniverse noutra máquina, estes itens **não vêm pelo git** e precisam ser recriados:

1. **`.vault`** — `GITHUB_TOKEN=` + `GITHUB_TOKEN_LAB=` + `GROQ_API_KEY=` + `TELEGRAM_TOKEN=` + `SOL_CHAT_ID=`. Sem ele, nada autentica.
2. **Chave SSH `~/.ssh/vscode_key`** — cadastrada na Polaris via extensão Hostinger do VS Code. `root@195.200.5.145` porta 22.
3. **Submodule** — `git submodule update --init` após clonar.
4. **Credencial git de push** — configurar token no `.git/config`.
