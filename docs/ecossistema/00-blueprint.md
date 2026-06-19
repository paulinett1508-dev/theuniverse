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

## Instância isolada, ideia compartilhada — o universo conspira a favor

Isolamento ≠ ilhamento. A distinção é entre **instância** e **receita**:

- **Instância** (local, isolada): o satélite concreto — código, dados, motor — de um planeta. Órbita exclusiva. Nunca serve outro planeta.
- **Receita** (universal, replicável): a arquitetura/abordagem que fez aquele satélite funcionar. Quando uma ideia roda bem num planeta, ela **pode e deve** ser replicada em qualquer outro, **dadas suas proporções**.

Não se reinventa o que já foi validado. Uma vitória num planeta vira conhecimento coletivo — sobe pra **gravidade** (agnostic-core) como skill/template, e desce em cada planeta ajustada ao seu tamanho e stack.

> Exemplo: o **Hermes-Oráculo** nasce no nexus/Lab. Validado, sua receita sobe à gravidade. Outro planeta ganha o *seu* oráculo — instância nova, isolada, nas suas proporções. Mesmo padrão, motores diferentes.

## Decisões travadas

- **Casa do satélite**: dentro do próprio planeta (pasta/submodule no repo). Motor nasce e morre com o planeta.
- **Núcleo na VPS Oráculo** (`2.25.163.125`, SSH :49222), reaproveitando o motor Hermes (ingestor + RAG + MCP já instalados em `/opt/hermes-*`).

## Os dois fluxos — o universo nunca afeta a vida dos planetas

| fluxo | direção | natureza | toca o planeta? |
|---|---|---|---|
| **Observação** | universo ← planetas | só **leitura** (API) → vira ficha | ❌ nunca |
| **Gravidade** | agnostic-core → planetas | **opt-in** (o planeta puxa o submodule) | só se o planeta quiser |

O único `git push` que existe é **no theuniverse** (as observações). Jamais se empurra código pra dentro de outro repo. O guardião lê tudo, escreve só em casa.

### O Censo
Rotina que materializa a Observação: lista todos os repos (API), faz diff contra `planets/`, detecta 🆕 novos / 💥 explodidos / 🔄 mudanças, atualiza fichas + índice + changelog, commita **só no theuniverse**.

- **Cadência**: agendado (GitHub Actions, cron diário). Token vive como *secret* `UNIVERSE_PAT`, nunca no código.
- Planeta novo é **auto-descoberto** — o Sol não precisa anunciar.
- *(futuro)* quando o Hermes-Oráculo existir, o Censo notifica via Telegram: "novo planeta detectado".

## Subsistemas (ordem de construção)

| # | Subsistema | Papel | Depende de | Status |
|---|---|---|---|---|
| **A** | Hermes-Bot (canal) | Bot Telegram ↔ motor Hermes. Fundação da comunicação | — | 🔜 próximo ciclo |
| **B** | Sistema Nervoso (notificar) | Eventos observados (API) → Telegram. Roda no theuniverse (Actions), não na Polaris | A (só o bot) | 📋 spec aprovado |
| **C** | Guardião da Galáxia (segurança) | Curadoria de skills + varredura local + escudos | A, B | ⏳ |
| **D** | Satélites Naturais (helpers locais) | Motor de IA por planeta (nebuloso, refino próprio) | A, B | ⏳ |

Cada subsistema = seu próprio ciclo spec → plano → implementação.
