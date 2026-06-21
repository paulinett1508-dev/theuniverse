# Dashboard Galáctica v2 — Spec

> Objetivo: elevar a vista galáctica de "esferas coloridas" para um sistema solar vivo,
> com cada corpo celeste visualmente fiel à sua classe astronômica real.
> A nova taxonomia substitui os tipos atuais (planet/station/satellite/…)
> por uma classificação baseada na Via Láctea e no Sistema Solar.

---

## 1. Nova Taxonomia Astronômica

### Critérios de classificação

| dimensão | métrica no repo |
|---|---|
| **Massa** | diskKB (tamanho do repo) |
| **Temperatura** | frequência de commits (últimos 90 dias) |
| **Luminosidade** | estrelas + forks + contribuidores |
| **Tipo espectral** | cluster semântico (infra, produto, showcase, legado…) |
| **Estado evolutivo** | saudável / warning / crítico / arquivado |

### Tabela de tipos

| classe | emoji | nome | critério | repos candidatos |
|---|---|---|---|---|
| **estrela-de-neutrons** | ⚡ | Estrela de Nêutrons | pequeno mas gravítico — dependência crítica de outros repos | `agnostic-core` |
| **gigante-gasoso** | 🌀 | Gigante Gasoso | grande (>5 MB), ativo, muitas linguagens / muitos arquivos | `sbrgestao`, `nexus-labsobral`, `SuperCartolaManagerv5` |
| **planeta-rochoso** | 🪨 | Planeta Rochoso | tamanho médio, funcionalidade sólida e delimitada | maioria dos repos de produto |
| **ana-vermelha** | 🔴 | Anã Vermelha | pequeno, pouco ativo mas estável e de longa vida | repos de landing page, repos dormentes saudáveis |
| **planeta-oceano** | 🌊 | Planeta Oceano | repo de dados / API-heavy / banco | repos com sufixo `-api`, `-db`, integrações externas |
| **planeta-gelado** | 🧊 | Planeta Gelado | baixa atividade, tamanho médio, sem commits há >90 dias | repos em hibernação |
| **lua** | 🌑 | Lua | satélite de outro repo — dependente ou extensão direta | `luna-base`, repos `*-plugin`, `*-extension` |
| **satelite-artificial** | 🛸 | Satélite Artificial | helper/dispatcher criado para orbitar o ecossistema | `mcp-eventos` |
| **nebulosa** | 🌌 | Nebulosa | repo em formação — <30 dias ou ainda sem estrutura definida | repos recém-criados |
| **supernova** | 💥 | Supernova | condenado ao arquivamento — declarado pelo TheGod | `bolaocopa2026`, `f1-pulse` |
| **buraco-negro** | 🕳️ | Buraco Negro | arquivado mas ainda referenciado por outros repos | repos arquivados com dependentes |
| **planeta-toys** | 🎮 | Planeta Toys | repo de entretenimento / joguinhos / experimento lúdico | `vibegaminghub` |

> **Regra**: a classificação automática usa massa + temperatura + luminosidade.
> O TheGod pode forçar qualquer tipo via `SPECIAL_BODIES` em `api/planets.js`.

---

## 2. Renderização Three.js por Tipo

Cada classe tem geometria, material e animação próprios.
Tamanho base calculado pelo `magnitude` (1–5), mas com ranges distintos por classe.

### ⚡ Estrela de Nêutrons (`estrela-de-neutrons`)

- **Geometria**: `IcosahedronGeometry(r, 2)` — facetado, denso
- **Material**: `MeshStandardMaterial` emissivo branco-azulado, `emissiveIntensity` pulsante (2 Hz)
- **Efeito extra**: campo magnético — dois arcos (`TubeGeometry` sobre curva Bezier) girando nos eixos X e Z
- **Cor**: branco → azul elétrico
- **Animação**: pulso de emissividade rápido + rotação lenta no eixo Y

### 🌀 Gigante Gasoso (`gigante-gasoso`)

- **Geometria**: `SphereGeometry(r, 64, 32)` — alta subdivisão para suavidade
- **Material**: `MeshPhongMaterial` com vertex shader deslocando bandas horizontais (simulate via textura canvas procedural)
- **Textura**: canvas 256×128 com bandas horizontais de cores análogas (laranja, marrom, creme para sbrgestao; azul, cinza, branco para repos frios)
- **Anéis**: `TorusGeometry` para repos com `magnitude >= 4` — anel único translúcido
- **Tamanho**: range 12–22 unidades (maior que planetas rochosos)
- **Animação**: rotação rápida (período 8s), bandas deslocam lentamente

### 🪨 Planeta Rochoso (`planeta-rochoso`)

- **Geometria**: `SphereGeometry(r, 32, 16)` com perturbação de vértices via noise (simula superfície irregular)
- **Material**: `MeshPhongMaterial` textura procedural de crateras (círculos escuros sobre base sólida)
- **Cor**: determinística por nome (paleta atual — mantém identidade visual)
- **Tamanho**: range 4–10 unidades
- **Animação**: rotação lenta (período 25s)

### 🔴 Anã Vermelha (`ana-vermelha`)

- **Geometria**: `SphereGeometry(r, 24, 12)` — menor
- **Material**: `MeshPhongMaterial` vermelho-alaranjado com emissividade baixa (0.3)
- **Glow sprite**: raio 4× (mais suave, menos intenso que planetas rochosos)
- **Tamanho**: range 3–6 unidades
- **Animação**: rotação muito lenta

### 🌊 Planeta Oceano (`planeta-oceano`)

- **Geometria**: `SphereGeometry(r, 48, 24)`
- **Material**: textura canvas — oceano em movimento (noise sinusoidal em azul-verde)
- **Efeito**: nuvens como segundo `SphereGeometry(r*1.04)` semi-transparente branco
- **Cor dominante**: azul profundo, turquesa
- **Animação**: nuvens rotacionam mais devagar que a superfície

### 🧊 Planeta Gelado (`planeta-gelado`)

- **Geometria**: `SphereGeometry(r, 32, 16)`
- **Material**: branco-azulado metálico, `MeshStandardMaterial({metalness:.3, roughness:.7})`
- **Efeito**: partículas de gelo ao redor (`PointCloud` esparso na órbita)
- **Cor**: branco neve, azul-gelo
- **Animação**: rotação lenta, partículas orbitam devagar

### 🌑 Lua (`lua`)

- **Geometria**: `SphereGeometry(r, 32, 16)` + perturbação de crateras (idem rochoso)
- **Material**: cinza-azulado, sem emissividade
- **Efeito extra**: trilha pontilhada ao redor do planeta pai (linha tracejada na órbita)
- **Tamanho**: range 3–6 unidades
- **Posicionamento**: anel mais interno, velocidade orbital mais alta

### 🛸 Satélite Artificial (`satelite-artificial`)

- **Geometria**: `OctahedronGeometry(r)` — diamante
- **Material**: `MeshStandardMaterial({metalness:.8, roughness:.2})` prateado
- **Efeito extra**: dois painéis solares (`BoxGeometry` achatado) perpendiculares ao eixo
- **Animação**: rotação no eixo Y (período 6s), painéis ficam fixos no plano XZ

### 🌌 Nebulosa (`nebulosa`)

- **Geometria**: sem mesh central sólido — apenas nuvem de partículas
- **Efeito**: `PointCloud` esférico com 200 partículas, opacidade 0.4, escala grande
- **Cor**: baseada no cluster semântico (lilás para infra, verde para produto, etc.)
- **Animação**: expansão/contração lenta + rotação do PointCloud

### 💥 Supernova (`supernova`)

- **Geometria**: `SphereGeometry(r, 32, 16)` central + anéis de explosão
- **Material**: `MeshStandardMaterial` emissivo laranja-vermelho intenso (`emissiveIntensity` variável)
- **Efeito extra**: partículas divergindo do centro (200 partículas acelerando para fora, reset ao raio máximo)
- **Animação**: pulso muito rápido (1.5 Hz), partículas orbitam caoticamente

### 🕳️ Buraco Negro (`buraco-negro`)

- **Geometria**: esfera central preta `r=1` + disco de acreção (`TorusGeometry` fino, inclinado 20°)
- **Material**: esfera = preto absoluto (`MeshBasicMaterial({color:0x000000})`); disco = emissivo âmbar-laranja
- **Efeito extra**: lensing gravitacional — distorção visual simulada com sprite de glow elíptico
- **Animação**: disco gira rápido (período 3s)

### 🎮 Planeta Toys (`planeta-toys`)

- **Geometria**: `SphereGeometry(r, 48, 24)`
- **Material**: shader de gradiente animado — hue-rotate contínuo (canvas texture atualizado a cada frame)
- **Cor**: rosa → roxo → azul ciclando
- **Glow sprite**: grande (raio 8×), cor muda junto com o hue

---

## 3. Sistema de Tamanho Global

| classe | range (unidades Three.js) |
|---|---|
| Estrela de Nêutrons | 14–18 (fixo, não varia por magnitude) |
| Gigante Gasoso | 12–22 |
| Planeta Rochoso | 4–10 |
| Anã Vermelha | 3–6 |
| Planeta Oceano | 5–11 |
| Planeta Gelado | 4–9 |
| Lua | 3–5 |
| Satélite Artificial | 5–7 |
| Nebulosa | 8–14 (nuvem, sem massa central) |
| Supernova | 8–16 (pulsante) |
| Buraco Negro | disco 12–20, núcleo 1–2 |
| Planeta Toys | 6–12 |

---

## 4. Distribuição em Anéis

Manter os 4 anéis atuais. Critérios de posicionamento por classe:

| anel | distância | candidatos preferenciais |
|---|---|---|
| 0 (mais interno) | 120u | Satélite Artificial, Luas, Nebulosas recentes |
| 1 | 210u | Anãs Vermelhas, Planetas Gelados, Buraco Negro |
| 2 | 310u | Planetas Rochosos, Oceano, Toys |
| 3 (mais externo) | 414u | Gigantes Gasosos, Supernovas |

Estrela de Nêutrons (`agnostic-core`): posição fixa entre o Sol e o anel 0 (como estação atual), não orbita.

---

## 5. Classificação Automática (lógica em `api/planets.js`)

```
function classifyBody(planet) {
  if (SPECIAL_BODIES[planet.name]) return SPECIAL_BODIES[planet.name]

  const mb = planet.diskKB || 0
  const age = daysSinceCommit(planet.lastCommit)
  const hot = planet.recentCommits > 10   // últimos 90 dias

  if (mb > 5000 && hot)            return 'gigante-gasoso'
  if (mb > 5000 && !hot)           return 'planeta-gelado'
  if (mb < 500 && age > 180)       return 'ana-vermelha'
  if (age < 30)                    return 'nebulosa'
  if (isDataRepo(planet))          return 'planeta-oceano'
  return 'planeta-rochoso'          // default
}
```

`SPECIAL_BODIES` (hardcoded, sobrescreve tudo):
```js
agnostic-core   → estrela-de-neutrons
mcp-eventos     → satelite-artificial
luna-base       → lua
vibegaminghub   → planeta-toys
bolaocopa2026   → supernova
f1-pulse        → supernova
```

---

## 6. Paleta Cromática por Cluster Semântico

Planetas rochosos e oceano herdam cor base do cluster:

| cluster | tom base |
|---|---|
| infra / core | azul aço |
| produto SaaS | verde esmeralda |
| showcase / LP | dourado / âmbar |
| entretenimento | roxo / magenta |
| saúde / clínica | verde-menta |
| legado / arquivado | cinza desbotado |

---

## 7. Plano de Implementação

### Fase 1 — Taxonomia (sem Three.js)
- Atualizar `api/planets.js`: `classifyBody()` + novos `SPECIAL_BODIES`
- Atualizar CSS dos cards 2D para novos tipos
- Atualizar `ESTADO.md` com nova taxonomia

### Fase 2 — Three.js geometrias
- Implementar `buildMesh(planet)` com switch por tipo
- Prioridade: rochoso (default), gigante-gasoso, estrela-de-neutrons, supernova
- Manter glow sprites — só trocar geometria base

### Fase 3 — Efeitos avançados
- Texturas canvas procedurais (gigante-gasoso, oceano)
- Partículas (supernova, nebulosa, gelado)
- Painéis solares (satélite), arcos magnéticos (estrela-de-neutrons)
- Disco de acreção (buraco-negro)

### Fase 4 — Animações globais
- Sistema de respawn de partículas
- Nuvem orbital do planeta oceano
- Hue-rotate do toys sincronizado com frame clock

---

## 8. O que NÃO muda

- Distribuição angular uniforme por anel (já implementada e funciona)
- Responsive camera `_posCamera()` (já ok)
- Raycaster de seleção por planeta
- Torus de anéis orbitais
- Starfield e poeira cósmica
- Poll 8s de eventos ao vivo (shockwave, pulso CI)
- Cards 2D do dashboard orbital (vista padrão — não é afetada)
