# ESTADO DO UNIVERSO — Handoff entre sessões

> **Documento auto-suficiente.** Tudo para retomar o trabalho está aqui — não é preciso colar nada da sessão anterior nem lembrar de nada externo. Este arquivo é injetado automaticamente no contexto a cada sessão (hook SessionStart). Ao lê-lo, você (o guardião) tem o universo inteiro na cabeça.
> Última atualização: 2026-06-20

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
| Fichas dos planetas | `planets/*.md` + `planets/_index.md` |
| Diário de bordo | `CHANGELOG.md` |
| Censo (auto-descoberta) | `scripts/censo.py` + `.github/workflows/censo.yml` |
| Credenciais (LOCAL, nunca no git) | `.vault` |

## Cosmologia (resumo — detalhe no CLAUDE.md)

O theuniverse é um **observatório pessoal** — olho omnisciente sobre TODOS os repos da conta `paulinett1508-dev` (e org `Lab-Sobral-Dev`). Observa, diagnostica, organiza. Nunca executa em outros repos.

O mundo **Matrix** (repo `the-matrix`) é um ecossistema separado do Laboratório Sobral com cosmologia própria (SHELDON, THEO, Hermes). Theuniverse observa seus repos de fora como qualquer outro planeta — sem acoplamento temático.

Gravidade = agnostic-core (submodule).

## Universo observável (2026-06-20)

**31 planetas** — 29 de `paulinett1508-dev` + 2 de `Lab-Sobral-Dev`.

**Excluídos do universo (decisão do TheGod):**
- `the-matrix`, `matrix-core` — mundo Matrix separado
- `baileys-whatsapp-server`, `bitrix-buddy-chat` — repos de terceiros (`rvsigor`)
- `nelly-miranda/*`, `VitorTDS/*` — colaborações pontuais de outros usuários

**Issues abertas a monitorar:** `SbrTask`×4 · `agnostic-core`×3 · `tokentown`×1 · `GessoExpress`×1

## ✅ Concluído nesta jornada

- **Sessão 2026-06-19/20 (máquina anterior):** Frota 100% mapeada · Subsistema B no ar · Subsistema A implementado (26 testes) · deploy travado em 1 decisão de token.
- **Sessão 2026-06-20 (esta máquina):**
  - `.vault` existia e funcionando (`GITHUB_TOKEN` + `GROQ_API_KEY`)
  - Universo remapeado: contexto Matrix separado, `Lab-Sobral-Dev` incluído, exclusões definidas
  - Fichas criadas: `SBR-ocomon-5.0`, `SbrTask`; removidas: `matrix-core`, `the-matrix`
  - `gh.py` atualizado: `UNIVERSE_OWNERS` filtra por owner (sem affiliation fixo)
  - `censo.py` atualizado: `EXCLUDE` list + clusters novos
  - Censo rodado e pushado — 31 planetas, índice limpo

## 🔴 FRENTES ABERTAS — retomar aqui

### 1. Hermes-Oráculo (subsistema A) — ✅ NO AR (2026-06-20)

Deploy concluído na Polaris (`195.200.5.145`). Respondendo no Telegram via `@guardiao_universo_bot`. 227 chunks indexados. Long-polling ativo como serviço systemd.

**Infra da Polaris (nosso universo — NÃO confundir com Matrix):**
- IP: `195.200.5.145` · SSH porta 22 · chave `~/.ssh/vscode_key`
- Serviço: `systemctl status oraculo` · logs: `journalctl -u oraculo -f`
- Clone: `/opt/theuniverse` · venv: `/opt/oraculo/venv` · env: `/opt/oraculo/.env`
- Para atualizar: `git pull` em `/opt/theuniverse` + `systemctl restart oraculo`

**Para re-deploy do zero:** `bash oraculo/deploy.sh` (de dentro deste repo, na máquina local)

### 2. Subsistemas futuros (ordem C→D)

- **C** — Guardião da Galáxia (segurança): curadoria de skills + varredura local + escudos. Dívida: `hermes-dashboard.service` roda inseguro em `0.0.0.0:9119`.
- **D** — Satélites Naturais (motores IA locais por planeta). Nebuloso, precisa brainstorm próprio.

## Regras de ouro (não violar)

- Guardião **nunca** escreve em outro repo. Só observa (leitura) e escreve em casa (theuniverse).
- Mundo Matrix (`the-matrix`, `matrix-core`) = ecossistema separado. Observar de fora, não acoplar.
- Token vive só no `.vault` (local) e no `.git/config`. Nunca commitar.
- `UNIVERSE_OWNERS` em `gh.py` é o controle de escopo — alterar só com decisão do TheGod.

## 💻 Setup em novo computador (arquivos local-only, NÃO versionados)

Ao clonar o theuniverse noutra máquina, estes itens **não vêm pelo git** e precisam ser recriados:

1. **`.vault`** (raiz do repo, gitignorado) — `GITHUB_TOKEN=` e `GROQ_API_KEY=`. Sem ele, Censo/Sentinel/Oráculo não autenticam.
2. **Chave SSH `~/.ssh/vscode_key`** — cadastrada na Polaris via extensão Hostinger do VS Code. Porta 22, `root@195.200.5.145`.
3. **Submodule** — clonar com `git clone --recurse-submodules` (ou `git submodule update --init`).
4. **Credencial git de push** — configurar token no `.git/config` para conseguir `git push`.
