# ESTADO DO UNIVERSO — Handoff entre sessões

> **Documento auto-suficiente.** Tudo para retomar o trabalho está aqui — não é preciso colar nada da sessão anterior nem lembrar de nada externo. Este arquivo é injetado automaticamente no contexto a cada sessão (hook SessionStart). Ao lê-lo, você (o guardião) tem o universo inteiro na cabeça.
> Última atualização: 2026-06-20 (sessão noite)

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
| Spec Hermes-Oráculo (subsistema A) | `docs/ecossistema/A-hermes-oraculo-spec.md` |
| Spec Webhook Notifier (subsistema B2) | `docs/ecossistema/B2-webhook-notifier-spec.md` |
| Script escudos (C1) | `scripts/c1-update-github-ips.py` |
| Fichas dos planetas | `planets/*.md` + `planets/_index.md` |
| Diário de bordo | `CHANGELOG.md` |
| Censo (auto-descoberta) | `scripts/censo.py` + `.github/workflows/censo.yml` |
| Setup de webhooks | `scripts/setup-webhooks.py` |
| Credenciais (LOCAL, nunca no git) | `.vault` |

## Cosmologia (resumo — detalhe no CLAUDE.md)

O theuniverse é um **observatório pessoal** — olho omnisciente sobre TODOS os repos da conta `paulinett1508-dev`. Observa, diagnostica, organiza. Nunca executa em outros repos.

O mundo **Matrix** (repo `the-matrix`) é um ecossistema separado do Laboratório Sobral com cosmologia própria (SHELDON, THEO, Hermes). Theuniverse observa seus repos de fora como qualquer outro planeta — sem acoplamento temático.

Gravidade = agnostic-core (submodule).

## Universo observável (2026-06-20)

**27 planetas** — todos de `paulinett1508-dev`.

**Excluídos do universo (decisão do TheGod):**
- `the-matrix`, `matrix-core` — mundo Matrix separado
- `baileys-whatsapp-server`, `bitrix-buddy-chat` — repos de terceiros (`rvsigor`)
- `agnvendas-painelsbr`, `pedidomobile` — arquivados (funcionalidade absorvida por outros repos)
- `Lab-Sobral-Dev/*` — org fora de escopo; `SBR-ocomon-5.0` fadado ao arquivamento; `SbrTask` será migrado para `paulinett1508-dev/SbrTask` (futuro — censo captura automaticamente quando criado)

**Issues abertas a monitorar:** `agnostic-core`×3 · `tokentown`×1 · `GessoExpress`×1

## ✅ Concluído nesta jornada

- **Sessão 2026-06-19/20 (máquina anterior):** Frota 100% mapeada · Subsistema B no ar · Subsistema A implementado (26 testes).
- **Sessão 2026-06-20 (esta máquina):**
  - Universo remapeado: Matrix separado, Lab-Sobral-Dev incluído, exclusões definidas (31 planetas)
  - Hermes-Oráculo deployado na Polaris — Telegram respondendo via `@guardiao_universo_bot`
  - **Skill Sol** criada em `.agnostic-core/skills/automacao/sol-aquece-planetas.md` — testada em `botclinop`
  - **Subsistema B2 (Webhook Notifier)** deployado na Polaris porta 9120:
    - `webhook/receiver.py` — FastAPI + HMAC-SHA256
    - `scripts/setup-webhooks.py` — registra webhooks nos repos
    - 27/27 repos com webhook ativo → notificações Telegram em tempo real (push + PR)
  - **PAT renovado** (`theuniverse-master-key`) com scopes `repo` + `admin:repo_hook` + `admin:org_hook`
  - **Universo finalizado em 27 planetas**: Lab-Sobral-Dev removido de UNIVERSE_OWNERS; `agnvendas-painelsbr` e `pedidomobile` adicionados ao EXCLUDE
  - **Subsistema C implementado:**
    - C1 (Escudos): porta 9120 restrita aos 6 CIDRs oficiais do GitHub via UFW. Cron semanal (`.github/workflows/c1-update-ips.yml`) mantém IPs atualizados. **Pendente:** adicionar `POLARIS_SSH_KEY` nos secrets do GitHub Actions.
    - C2 (Secrets Scan): `sentinel.py` agora verifica `secret-scanning/alerts` em cada planeta. Novo evento `secret_exposto` notifica Telegram com tipo e link direto ao painel de segurança.

## 🔴 FRENTES ABERTAS — retomar aqui

### 1. Hermes-Oráculo (subsistema A) — ✅ NO AR

Deploy: Polaris `195.200.5.145`. Telegram: `@guardiao_universo_bot`. 227 chunks indexados.

**Infra da Polaris:**
- SSH: `ssh -i ~/.ssh/vscode_key root@195.200.5.145`
- Oráculo: `systemctl status oraculo` · `journalctl -u oraculo -f`
- Webhook: `systemctl status webhook` · `journalctl -u webhook -f`
- Clone: `/opt/theuniverse` · env: `/opt/oraculo/.env`
- Atualizar: `git pull` em `/opt/theuniverse` + `systemctl restart oraculo webhook`

**Re-deploy do zero:** `bash oraculo/deploy.sh` + `bash webhook/deploy.sh`

### 2. Subsistema B2 (Webhook Notifier) — ✅ NO AR

27 repos monitorados. Notifica push e PRs em tempo real via Telegram.
Para adicionar novo repo ao universo: `python scripts/setup-webhooks.py` após criar o repo.

### 3. Subsistema C — ✅ IMPLEMENTADO (2026-06-20)

- **C1 (Escudos):** UFW porta 9120 restrita aos CIDRs do GitHub. Cron semanal em `.github/workflows/c1-update-ips.yml`. **Pendente:** `POLARIS_SSH_KEY` nos secrets do GitHub para cron funcionar autônomo.
- **C2 (Secrets Scan):** sentinel detecta secrets expostos em qualquer planeta e notifica Telegram.

### 4. Subsistema D — DESCARTADO

Cada planeta decide sua própria IA se precisar. Não é responsabilidade do observatório.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse).
- Mundo Matrix (`the-matrix`, `matrix-core`) = ecossistema separado. Observar de fora, não acoplar.
- Token vive só no `.vault` (local) e no `/opt/oraculo/.env` (Polaris). Nunca commitar.
- `UNIVERSE_OWNERS` em `gh.py` é o controle de escopo — alterar só com decisão do TheGod.
- Após adicionar repo ao universo: rodar `python scripts/setup-webhooks.py` para registrar webhook.

## 💻 Setup em novo computador (arquivos local-only, NÃO versionados)

Ao clonar o theuniverse noutra máquina, estes itens **não vêm pelo git** e precisam ser recriados:

1. **`.vault`** — `GITHUB_TOKEN=` + `GROQ_API_KEY=` + `WEBHOOK_SECRET=`. Sem ele, nada autentica.
2. **Chave SSH `~/.ssh/vscode_key`** — cadastrada na Polaris via extensão Hostinger do VS Code. `root@195.200.5.145` porta 22.
3. **Submodule** — `git submodule update --init` após clonar.
4. **Credencial git de push** — configurar token no `.git/config`.
