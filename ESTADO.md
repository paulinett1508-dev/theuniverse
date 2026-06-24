# ESTADO DO UNIVERSO — Handoff entre sessões

> **Documento auto-suficiente.** Tudo para retomar o trabalho está aqui — não é preciso colar nada da sessão anterior nem lembrar de nada externo. Este arquivo é injetado automaticamente no contexto a cada sessão (hook SessionStart). Ao lê-lo, você (o guardião) tem o universo inteiro na cabeça.
> Última atualização: 2026-06-23 (Dashboard galáctica v6 + endpoint /ask M2M deployado)

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
| Fichas dos planetas | `planets/*.md` + `planets/_index.md` |
| Diário de bordo | `CHANGELOG.md` |
| Censo (auto-descoberta) | `scripts/censo.py` + `.github/workflows/censo.yml` |
| Setup de webhooks | `scripts/setup-webhooks.py` |
| Credenciais (LOCAL, nunca no git) | `.vault` |

## Cosmologia (resumo — detalhe no CLAUDE.md)

O theuniverse é um **observatório pessoal** — olho omnisciente sobre TODOS os repos da conta `paulinett1508-dev`. Observa, diagnostica, organiza. Nunca executa em outros repos.

O mundo **Matrix** (repo `the-matrix`) é um ecossistema separado do Laboratório Sobral com cosmologia própria (SHELDON, THEO, Hermes). Theuniverse observa seus repos de fora como qualquer outro planeta — sem acoplamento temático.

Gravidade = agnostic-core (submodule).

## Universo observável (2026-06-23)

**27+ planetas** — todos de `paulinett1508-dev`.

**Excluídos do universo (decisão do TheGod):**
- `the-matrix`, `matrix-core` — mundo Matrix separado
- `baileys-whatsapp-server`, `bitrix-buddy-chat` — repos de terceiros (`rvsigor`)
- `agnvendas-painelsbr`, `pedidomobile` — arquivados (na zona de decadência do BH)
- `Lab-Sobral-Dev/*` — org fora de escopo

**⚠️ Planeta novo detectado pelo censo:** `mybots-telegram` — não indexado ainda (ver issue #9)

**Issues abertas a monitorar:** `agnostic-core`×3 · `tokentown`×1 · `GessoExpress`×1
**CI com falha:** `sbrgestao` — `agnvendas-unit-tests failure` (Estrela da Morte ativa no dashboard)
**Supernovas iminentes:** `bolaocopa2026` · `f1-pulse` — arquivar/excluir quando TheGod decidir

## ✅ Concluído nesta jornada

### Sessão 2026-06-23 (esta)

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

- **Sentinel · Escudos:** UFW porta 9120 restrita aos CIDRs do GitHub. Cron semanal em `.github/workflows/c1-update-ips.yml`.
- **Sentinel · Farejador:** varredura de conteúdo por regex em todos os planetas, notifica Telegram e atualiza postura.

### 4. Dashboard NOC — ✅ NO AR | v6

URL: `theuniverse-lake.vercel.app` (Vercel, deploy automático no push).
Infra: `api/planets.js` + `api/events.js` (Vercel functions). Env var: `GITHUB_TOKEN` no painel Vercel.

**Corpos celestes especiais** (hardcoded em `api/planets.js → SPECIAL_BODIES`):
- station: `agnostic-core` · satellite: `mcp-eventos` · observatory: `luna-base`
- supernova: `bolaocopa2026`, `f1-pulse` · nebula: `vibegaminghub`

**Vista galáctica v6** (`dashboard/index.html` ~3050 linhas):
- 24 anéis orbitais, ring 0 = orbit 20u, ring 23 = orbit 375u
- Obi-Wan ISS: exílio `(80,120,60)`, wander autônomo quando idle (visita planetas por `bodyType==='planet'`)
- sentinel-core: satélite que orbita a ISS — fora do `actualMeshes`, não é planeta
- Zona de decadência (BH): todos os corpos com hitbox no raycaster (tooltip + card)
- Toggle de luzes da ISS: abrir painel Obi-Wan → botão "luzes: on/off"

**Novos planetas a adicionar ao mapa forçado:** `mybots-telegram` (ver issue #9)

### 5. Artoo — ✅ IMPLEMENTADO

`scripts/artoo.py` — abre Issues de alerta em planetas + notifica Telegram.
`scripts/carta_apresentacao.py` — enviada a 29/31 planetas.

### 6. mybots-telegram — ⏳ NÃO INDEXADO (issue #9)

Repo `mybots-telegram` detectado pelo censo. Ainda sem:
- Ficha em `planets/mybots-telegram.md`
- Entrada em `_GAL_FORCED_RING` ou posição no mapa galáxico
- Webhook registrado

### 7. sbrgestao CI — ⏳ ESTRELA DA MORTE (issue #10)

`agnvendas-unit-tests failure` — CI vermelho. Dashboard mostra alerta. Investigar antes de próxima sessão de produção.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse). Exceção explícita: **Artoo** (autorizado pelo TheGod) pode abrir Issues de alerta em planetas afetados.
- Mundo Matrix (`the-matrix`, `matrix-core`) = ecossistema separado. Observar de fora, não acoplar.
- Token vive só no `.vault` (local) e no `/opt/obi-wan/.env` (Polaris). Nunca commitar.
- `UNIVERSE_OWNERS` em `gh.py` é o controle de escopo — alterar só com decisão do TheGod.
- Após adicionar repo ao universo: rodar `python scripts/setup-webhooks.py` para registrar webhook.
- **Issue resolvida = comentar evidência (linhas de código) + fechar com `completed` imediatamente.**

## 💻 Setup em novo computador (arquivos local-only, NÃO versionados)

Ao clonar o theuniverse noutra máquina, estes itens **não vêm pelo git** e precisam ser recriados:

1. **`.vault`** — `GITHUB_TOKEN=` + `GROQ_API_KEY=` + `WEBHOOK_SECRET=`. Sem ele, nada autentica.
2. **Chave SSH `~/.ssh/vscode_key`** — cadastrada na Polaris via extensão Hostinger do VS Code. `root@195.200.5.145` porta 22.
3. **Submodule** — `git submodule update --init` após clonar.
4. **Credencial git de push** — configurar token no `.git/config`.
