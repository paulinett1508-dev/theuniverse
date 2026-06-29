# Obsidian Vault + Notas dos 10 Bots — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o theuniverse em um vault Obsidian completo e criar notas estruturadas para os 10 bots do universo (Obi-Wan, Artoo + 8 sentinelas).

**Architecture:** Adicionar `.obsidian/` de config mínima ao repo (rastreado no git, sem plugins); criar `bots/` com frontmatter YAML consistente com as fichas de planetas; adicionar [[wikilinks]] nos docs existentes que referenciam bots. Dataview faz o índice dinâmico — o `_index.md` estático de planetas tem equivalente em `bots/_index.md`.

**Tech Stack:** Markdown + YAML frontmatter, Obsidian (app local), plugins Dataview + obsidian-git (instalação manual pelo usuário — não rastreados no git).

## Global Constraints

- Frontmatter YAML: `tipo`, `nome`, `username`, `papel`, `status`, `token_secret`, `telegram_topic`, `script`, `workflow` — todos presentes em cada nota de bot
- Wikilinks no formato `[[caminho/relativo]]` sem extensão `.md`
- `.obsidian/plugins/` e arquivos de estado do Obsidian NUNCA no git
- Status dos bots sentinelas = `pendente` (tokens não criados ainda)
- Status dos bots Obi-Wan e Artoo = `ativo` (token `TELEGRAM_TOKEN` já existe)
- Não alterar fichas de planetas existentes (geradas pelo censo) — apenas `planets/sentinel-core.md` recebe link manual

---

## Mapa de Arquivos

| ação | arquivo | responsabilidade |
|---|---|---|
| criar | `.obsidian/app.json` | config do vault: wikilinks, pasta padrão |
| criar | `.obsidian/community-plugins.json` | lista de plugins habilitados |
| modificar | `.gitignore` | excluir runtime do Obsidian, manter config |
| criar | `bots/_index.md` | hub com Dataview query + tabela manual de fallback |
| criar | `bots/obi-wan.md` | nota do governante conversacional |
| criar | `bots/artoo.md` | nota do cão de guarda / mensageiro |
| criar | `bots/sentinelas/nervoso.md` | sentinel.py |
| criar | `bots/sentinelas/pulso.md` | pulso.py |
| criar | `bots/sentinelas/deps.md` | deps.py |
| criar | `bots/sentinelas/deploy.md` | deploy_health.py |
| criar | `bots/sentinelas/farejador.md` | secret_scan.py |
| criar | `bots/sentinelas/scout.md` | model_scout.py |
| criar | `bots/sentinelas/escudos.md` | c1-update-github-ips.py |
| criar | `bots/sentinelas/usage.md` | weekly-usage-notify.py |
| modificar | `ESTADO.md` | adicionar linha "Bots" na tabela "Onde está tudo" |
| modificar | `docs/ecossistema/A-obi-wan-spec.md` | link `[[bots/obi-wan]]` na linha do Bot |
| modificar | `planets/sentinel-core.md` | seção "Bots relacionados" com wikilinks |

---

## Task 1: Obsidian vault config + .gitignore

**Files:**
- Criar: `.obsidian/app.json`
- Criar: `.obsidian/community-plugins.json`
- Modificar: `.gitignore`

**Interfaces:**
- Produz: vault Obsidian funcional — TheuUniverse pode ser aberto como vault no app

- [ ] **Step 1: Criar `.obsidian/app.json`**

```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "attachmentFolderPath": "assets",
  "showUnsupportedFiles": false,
  "defaultViewMode": "preview"
}
```

- [ ] **Step 2: Criar `.obsidian/community-plugins.json`**

```json
["dataview", "obsidian-git"]
```

> Estes são os slugs dos plugins a instalar manualmente no Obsidian após abrir o vault. O arquivo apenas documenta quais plugins o vault usa — não os instala.

- [ ] **Step 3: Atualizar `.gitignore`**

Adicionar ao final do arquivo:

```
# Obsidian — runtime (não rastrear)
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/
.obsidian/cache
# rastreados: .obsidian/app.json, .obsidian/community-plugins.json
```

- [ ] **Step 4: Verificar**

```bash
git status
```
Esperado: `.obsidian/app.json` e `.obsidian/community-plugins.json` aparecem como untracked. `.obsidian/plugins/` não aparece.

- [ ] **Step 5: Commit**

```bash
git add .obsidian/app.json .obsidian/community-plugins.json .gitignore
git commit -m "feat(obsidian): vault config + gitignore"
```

---

## Task 2: `bots/_index.md` — hub Dataview

**Files:**
- Criar: `bots/_index.md`

**Interfaces:**
- Consome: frontmatter dos arquivos em `bots/` e `bots/sentinelas/` (criados nas Tasks 3 e 4)
- Produz: índice dinâmico de todos os bots via Dataview; tabela estática de fallback para leitura no GitHub

- [ ] **Step 1: Criar `bots/_index.md`**

```markdown
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
| [[bots/sentinelas/usage\|Claude Usage]] | `@universo_usage_bot` | uso Claude outbound | pendente | `TELEGRAM_TOKEN_USAGE` | `claude-usage` |

## Relacionado
- [[docs/ecossistema/A-obi-wan-spec]] — spec completo do Obi-Wan
- [[docs/ecossistema/00-blueprint]] — arquitetura do ecossistema
- [[planets/sentinel-core]] — repo onde vivem os bots
```

- [ ] **Step 2: Commit**

```bash
git add bots/_index.md
git commit -m "feat(bots): _index.md com Dataview + tabela estática"
```

---

## Task 3: Notas Obi-Wan e Artoo

**Files:**
- Criar: `bots/obi-wan.md`
- Criar: `bots/artoo.md`

**Interfaces:**
- Consome: spec `docs/ecossistema/A-obi-wan-spec.md`, código `scripts/artoo.py`
- Produz: notas linkáveis dos dois bots especiais com wikilinks bidirecionais

- [ ] **Step 1: Criar `bots/obi-wan.md`**

```markdown
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

O governante do universo. Canal bidirecional entre [[user_sol|TheGod]] e o ecossistema via Telegram. Único bot que **recebe** mensagens — todos os outros só enviam.

## Identidade

| campo | valor |
|---|---|
| username | `@guardiao_universo_bot` |
| papel | conversacional inbound |
| runtime | systemd na Polaris (long-polling) |
| cérebro | Groq Llama 70B (`llama-3.3-70b-versatile`) |
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
```

- [ ] **Step 2: Criar `bots/artoo.md`**

```markdown
---
tipo: bot
nome: Artoo
username: artoo_universo_bot
papel: mensageiro
status: pendente
token_secret: TELEGRAM_TOKEN_ARTOO
telegram_topic: alertas
script: scripts/artoo.py
workflow: acionado por scripts/sentinel.py (ci_falhou)
---

# Artoo — Cão de Guarda / Mensageiro Cósmico

O cão de guarda de [[bots/obi-wan|Obi-Wan]]. Quando o observatório detecta uma ameaça num planeta, Artoo atravessa a órbita e entrega um alerta diretamente no mundo deles via GitHub Issue — o planeta não sabe da ameaça até Artoo chegar.

## Identidade

| campo | valor |
|---|---|
| username | `@artoo_universo_bot` (pendente criação) |
| papel | mensageiro / ação outbound |
| acionado por | [[scripts/sentinel.py]] — evento `ci_falhou` |
| notifica | Telegram tópico `alertas` + GitHub Issue no planeta afetado |

## Personalidade (evolui com missões)

| nível | missões |
|---|---|
| novice | 0–9 |
| journeyman | 10–49 |
| veteran | 50+ |

Estado em: `state/artoo-state.json`

## O que faz

1. Recebe repo + reason + detail do [[bots/sentinelas/nervoso|Sistema Nervoso]]
2. Abre GitHub Issue no planeta afetado com label `observatory-alert`
3. Envia notificação Telegram no tópico `alertas`

## Relacionado

- [[bots/obi-wan]] — quem guarda
- [[bots/sentinelas/nervoso]] — quem aciona
- [[bots/_index]] — todos os bots
- [[planets/sentinel-core]] — repo onde vive
```

- [ ] **Step 3: Commit**

```bash
git add bots/obi-wan.md bots/artoo.md
git commit -m "feat(bots): notas Obi-Wan e Artoo"
```

---

## Task 4: 8 notas dos sentinelas

**Files:**
- Criar: `bots/sentinelas/nervoso.md`
- Criar: `bots/sentinelas/pulso.md`
- Criar: `bots/sentinelas/deps.md`
- Criar: `bots/sentinelas/deploy.md`
- Criar: `bots/sentinelas/farejador.md`
- Criar: `bots/sentinelas/scout.md`
- Criar: `bots/sentinelas/escudos.md`
- Criar: `bots/sentinelas/usage.md`

**Interfaces:**
- Consome: `scripts/sentinel.py` (TOPICS dict), workflows em `.github/workflows/`
- Produz: 8 notas com frontmatter completo, linkáveis no graph view

- [ ] **Step 1: Criar `bots/sentinelas/nervoso.md`**

```markdown
---
tipo: bot
nome: Sistema Nervoso
username: universo_nervoso_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_NERVOSO
telegram_topic: sentinel
script: scripts/sentinel.py
workflow: .github/workflows/sentinel.yml
---

# Sistema Nervoso

Observa todos os repos do universo a cada 15min. Detecta: novos planetas, planetas sumidos, CI com falha, issues novas, segredos expostos. Aciona [[bots/artoo|Artoo]] automaticamente em `ci_falhou`.

## Cadência

`*/15 * * * *` — a cada 15 minutos

## Eventos detectados

| evento | destino |
|---|---|
| `novo_planeta` | Telegram tópico `sentinel` |
| `planeta_sumido` | Telegram tópico `sentinel` |
| `ci_falhou` | Telegram tópico `sentinel` + aciona [[bots/artoo]] |
| `issue_nova` | Telegram tópico `sentinel` |
| `secret_exposto` | Telegram tópico `sentinel` |
| heartbeat | Telegram tópico `sentinel` |

## Estado persistido

`state/sentinel-state.json` (commitado no repo via workflow)

## Relacionado

- [[bots/_index]]
- [[bots/artoo]] — cão de guarda que aciona
- [[planets/sentinel-core]]
```

- [ ] **Step 2: Criar `bots/sentinelas/pulso.md`**

```markdown
---
tipo: bot
nome: Pulso
username: universo_pulso_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_PULSO
telegram_topic: pulso
script: scripts/pulso.py
workflow: .github/workflows/pulso.yml
---

# Pulso — Uptime dos Planetas

Monitora o status de uptime de todos os planetas com URL pública a cada 15min. Notifica mudanças de estado (up→down, down→up).

## Cadência

`*/15 * * * *` — a cada 15 minutos

## Estado persistido

`state/pulso-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
```

- [ ] **Step 3: Criar `bots/sentinelas/deps.md`**

```markdown
---
tipo: bot
nome: Deps
username: universo_deps_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_DEPS
telegram_topic: deps
script: scripts/deps.py
workflow: .github/workflows/deps.yml
---

# Deps — CVEs nos Planetas

Varre dependências de todos os repos diariamente, detectando CVEs e vulnerabilidades conhecidas via GitHub Dependabot alerts.

## Cadência

`0 6 * * *` — diário às 06h UTC

## Estado persistido

`state/deps-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
```

- [ ] **Step 4: Criar `bots/sentinelas/deploy.md`**

```markdown
---
tipo: bot
nome: Deploy Health
username: universo_deploy_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_DEPLOY
telegram_topic: deploy
script: scripts/deploy_health.py
workflow: .github/workflows/deploy-health.yml
---

# Deploy Health — Saúde dos Deploys

Monitora o status dos últimos deploys de todos os repos a cada 30min. Detecta deploys com falha ou regressões.

## Cadência

`*/30 * * * *` — a cada 30 minutos

## Estado persistido

`state/deploy-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
```

- [ ] **Step 5: Criar `bots/sentinelas/farejador.md`**

```markdown
---
tipo: bot
nome: Farejador
username: universo_farejador_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_FAREJADOR
telegram_topic: seguranca
script: scripts/secret_scan.py
workflow: .github/workflows/secret-audit.yml
---

# Farejador — Varredura de Segredos

Complementa o GitHub secret-scanning nativo com regex de conteúdo customizado. Varre todos os repos diariamente em busca de segredos hardcoded não detectados pelo GitHub.

## Cadência

`30 9 * * *` — diário às 09h30 UTC (~06h30 BRT)

## Estado persistido

`state/secret-scan-state.json` + `state/posture-status.json` (commitados no repo)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
```

- [ ] **Step 6: Criar `bots/sentinelas/scout.md`**

```markdown
---
tipo: bot
nome: Model Scout
username: universo_scout_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_SCOUT
telegram_topic: model-scout
script: scripts/model_scout.py
workflow: .github/workflows/model-scout.yml
---

# Model Scout — Radar de Modelos IA

Monitora novos modelos disponíveis na Groq API toda segunda-feira. Notifica quando modelos novos aparecem ou quando modelos usados pelo ecossistema são descontinuados.

## Cadência

`0 8 * * 1` — toda segunda-feira às 08h UTC

## Estado persistido

`state/model-state.json` (cache GitHub Actions)

## Relacionado

- [[bots/_index]]
- [[planets/sentinel-core]]
- [[planets/hermes]] — usa modelos Groq
```

- [ ] **Step 7: Criar `bots/sentinelas/escudos.md`**

```markdown
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
```

- [ ] **Step 8: Criar `bots/sentinelas/usage.md`**

```markdown
---
tipo: bot
nome: Claude Usage
username: universo_usage_bot
papel: outbound-notifier
status: pendente
token_secret: TELEGRAM_TOKEN_USAGE
telegram_topic: claude-usage
script: scripts/weekly-usage-notify.py
workflow: N/A (cron local na máquina dev)
---

# Claude Usage — Monitor de Uso do Claude Code

Notifica o uso semanal do Claude Code (tokens/custo). Digest a cada 2h entre 05h–23h; alerta de threshold 1x/dia quando o gasto semanal ultrapassa o limite configurado.

## Cadência

Cron local na máquina dev (não Actions) — configurado via `setup-claude-usage.ps1`.

## Config

Lê limite de `weekly-limit.json` (path configurável por máquina via `.vault`).

## Relacionado

- [[bots/_index]]
- [[planets/theuniverse]]
```

- [ ] **Step 9: Commit**

```bash
git add bots/sentinelas/
git commit -m "feat(bots): 8 notas dos sentinelas"
```

---

## Task 5: Wikilinks nos docs existentes

**Files:**
- Modificar: `ESTADO.md` (tabela "Onde está tudo")
- Modificar: `docs/ecossistema/A-obi-wan-spec.md` (linha do Bot)
- Modificar: `planets/sentinel-core.md` (seção "Notas do guardião")

**Interfaces:**
- Consome: notas criadas nas Tasks 3 e 4
- Produz: backlinks bidirecionais no graph view do Obsidian

- [ ] **Step 1: Atualizar `ESTADO.md` — tabela "Onde está tudo"**

Adicionar linha após a linha de `Sentinel · Escudos (C1)`:

```markdown
| Bots do Universo (10 bots) | `bots/` + `bots/_index.md` |
```

- [ ] **Step 2: Atualizar `docs/ecossistema/A-obi-wan-spec.md`**

Localizar a linha:
```
| Bot | **mesmo `guardiao_universo_bot` do B** — B só faz `sendMessage` ...
```

Substituir por:
```
| Bot | [[bots/obi-wan\|`guardiao_universo_bot`]] — inbound only (sentinelas têm bots próprios) |
```

- [ ] **Step 3: Atualizar `planets/sentinel-core.md`**

Na seção `## Notas do guardião`, substituir o comentário placeholder por:

```markdown
## Notas do guardião

Repo central dos bots do universo. Cast completo:

- [[bots/obi-wan]] — governante conversacional (inbound)
- [[bots/artoo]] — cão de guarda / mensageiro
- [[bots/sentinelas/nervoso]] · [[bots/sentinelas/pulso]] · [[bots/sentinelas/deps]]
- [[bots/sentinelas/deploy]] · [[bots/sentinelas/farejador]] · [[bots/sentinelas/scout]]
- [[bots/sentinelas/escudos]] · [[bots/sentinelas/usage]]

Índice completo: [[bots/_index]]
```

- [ ] **Step 4: Commit final**

```bash
git add ESTADO.md docs/ecossistema/A-obi-wan-spec.md planets/sentinel-core.md
git commit -m "docs: wikilinks nos docs existentes — fecha migração Obsidian"
```

---

## Self-Review

### Spec coverage
- ✅ Vault Obsidian configurado (Task 1)
- ✅ 10 bots documentados (Tasks 3+4)
- ✅ Dataview query + tabela fallback (Task 2)
- ✅ Wikilinks bidirecionais (Task 5)
- ✅ Artoo como cão de guarda do Obi-Wan (bots/artoo.md)
- ✅ Status `pendente` para bots sem token ainda
- ✅ `telegram_topic` novo por sentinela (não compartilhado)

### Pending (fora deste plano — próxima frente)
- Criação dos 10 bots no BotFather (ação do TheGod)
- Migração dos scripts para usar tokens individuais (plano separado)
- Criação dos novos tópicos Telegram (ação do TheGod)

### Placeholder scan
- Nenhum TBD/TODO nos arquivos criados
- Tokens marcados como `pendente` explicitamente
- IDs de tópicos Telegram marcados via nome (não IDs numéricos — aguardam criação)
