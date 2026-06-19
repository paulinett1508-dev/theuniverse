# theuniverse — Diário de Bordo

Registro de eventos cósmicos: nascimentos, explosões, fusões e migrações de planetas.

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
