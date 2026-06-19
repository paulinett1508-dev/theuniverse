# Blueprint do Ecossistema de Comunicação

> Constituição macro da comunicação SOL ↔ Universo.
> Irmã do `the-matrix` — aqui se define **como** o universo conversa, não o que cada planeta faz.
> Princípio reitor: **ADR-001 the-matrix — federação, não anexação.**

## Princípio fundador

**Separar transporte de inteligência.**

O que é universal é o *trilho* (como se comunica). O que é local é o *motor* (a inteligência aplicada). Um satélite orbita UM planeta — nunca compartilha. Na história recente do universo, satélites nunca compartilharam planetas.

## As 3 camadas

```
☀️ SOL (humano) ──Telegram──►
        │
┌───────▼──────────────────────────────────────────────┐
│ CAMADA 1 — NÚCLEO DE COMUNICAÇÃO (universal, burro)   │
│ Hermes-Bot + barramento de eventos · VPS Oráculo      │
│ Só transporte. Não sabe nada sobre nenhum planeta.    │
└───────┬───────────────────────────────────────────────┘
        │ protocolo comum (contrato matrix-core / Zod)
   ┌────┼────┐
┌──▼──┐ ┌─▼──┐  ┌─ planeta sem satélite: fala direto ─┐
│SAT A│ │SAT B│  └──────────────────────────────────────┘
│ ⊙ X │ │ ⊙ Y │   CAMADA 3 — SATÉLITES (local, isolados)
└─────┘ └─────┘   motor dentro do próprio planeta,
                  órbita exclusiva. SAT A nunca toca Y.

CAMADA 2 — GUARDIÃO DA GALÁXIA (padrão universal, aplicação local)
skills de segurança no agnostic-core (gravidade);
cada planeta varre o próprio stack com o próprio escudo.
```

## Regra de ouro

| Compartilhado (universal) | Soberano de cada planeta (local) |
|---|---|
| **Trilho** — canal Telegram/bot | **Motor** — a IA local do satélite |
| **Protocolo** — contrato de como se fala (matrix-core/Zod) | **Órbita** — um satélite, um planeta |
| **Gravidade** — skills/padrões do agnostic-core | **Escudo aplicado** — varredura adaptada ao stack |

O universo compartilha **como se comunica e quais padrões segue** — jamais **a inteligência que pensa por cada planeta**.

## Decisões travadas

- **Casa do satélite**: dentro do próprio planeta (pasta/submodule no repo). Motor nasce e morre com o planeta.
- **Núcleo na VPS Oráculo** (`2.25.163.125`, SSH :49222), reaproveitando o motor Hermes (ingestor + RAG + MCP já instalados em `/opt/hermes-*`).

## Subsistemas (ordem de construção)

| # | Subsistema | Papel | Depende de | Status |
|---|---|---|---|---|
| **A** | Hermes-Bot (canal) | Bot Telegram ↔ motor Hermes. Fundação da comunicação | — | 🔜 próximo ciclo |
| **B** | Sistema Nervoso (notificar tudo) | Eventos dos planetas → barramento → bot | A | ⏳ |
| **C** | Guardião da Galáxia (segurança) | Curadoria de skills + varredura local + escudos | A, B | ⏳ |
| **D** | Satélites Naturais (helpers locais) | Motor de IA por planeta (nebuloso, refino próprio) | A, B | ⏳ |

Cada subsistema = seu próprio ciclo spec → plano → implementação.
