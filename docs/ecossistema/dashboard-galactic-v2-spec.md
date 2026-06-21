# Dashboard Galáctica v2 — Spec

> Objetivo: elevar a vista galáctica de "esferas coloridas" para um sistema solar vivo,
> com cada corpo celeste visualmente fiel à sua classe astronômica real.
> A nova taxonomia subdivide o tipo genérico "planet" em classes robustez-dependentes.
> Os corpos especiais existentes (station, satellite, observatory, supernova, toys)
> **não mudam de identidade** — só ganham visual mais rico.

---

## 0. Filosofia Visual — inspiração `solar-system.js`

O jogo `vibegaminghub/jogos/solar-system.js` (fiel ao original de @coding.stella)
usa uma ideia simples e poderosa:

> **Cada planeta = corpo real do sistema solar, com textura fotorrealista girando.**
> A textura não é decorativa — ela É o planeta. Rotação prograde vs retrógrada,
> velocidade distinta por planeta, a imagem saindo da tela em baixo.

### O que copiamos para a galáxia Three.js

1. **Textura por tipo** — cada classe de repo mapeia a um planeta/corpo real da Via Láctea
   e recebe uma textura procedural canvas que imita a fotografia NASA daquele corpo
   (bandas atmosféricas de Júpiter, superfície ferrugenta de Marte, gelo de Netuno, etc.)

2. **Rotação prograde/retrógrada** — planetas rochosos giram no sentido anti-horário
   (prograde); repos arquivados/legado giram no sentido horário (retrógrado, como Vênus)

3. **Velocidade de rotação proporcional ao nível de atividade** — repos com commits
   recentes giram mais rápido; repos dormentes giram devagar

4. **Textura sai da memória visual do observador** — o planeta deve parecer "real" ao
   olhá-lo de perto. No card lateral (canvas 2D já existente), a mesma textura é aplicada.

### Mapeamento tipo → corpo real

| classe do repo | corpo real | referência visual |
|---|---|---|
| gigante-gasoso | Júpiter | bandas laranja/marrom/creme + grande mancha vermelha |
| gigante-gelado | Netuno | azul profundo + banding sutil |
| planeta-rochoso (quente) | Marte | vermelho-ferrugem + crateras + calotas polares |
| planeta-rochoso (temperado) | Terra | azul + verde + nuvens brancas |
| planeta-rochoso (frio/dormente) | Lua / Mercúrio | cinza craterado, sem atmosfera |
| ana-vermelha | Vênus | laranja enevoado + camadas de nuvens espessas |
| planeta-oceano | Terra oceânica | predominância azul profundo + reflexo solar |
| planeta-gelado | Urano | azul-esverdeado liso com inclinação axial extrema |
| lua (satélite) | Lua | cinza escuro + crateras de impacto |
| satelite-artificial | — | metal polido (não é planeta, sem textura orgânica) |
| estrela-de-neutrons | Pulsar | branco-azul com campo magnético visível |
| supernova | Eta Carinae | plasma laranja-vermelho explodindo para fora |
| nebulosa | Nebulosa de Orion | nuvem gasosa colorida, sem superfície sólida |
| planeta-toys | — | gradiente sintético psicodélico (único que não imita natureza) |

### Implementação da textura (canvas procedural)

Cada tipo tem uma função `_paintTexture(ctx, w, h, seed)` que pinta num canvas 256×128.
Esse canvas vira um `THREE.CanvasTexture` aplicado ao `map` do material da esfera.
A esfera gira no eixo Y — a textura "rola" como no `solar-system.js`.

Exemplo de banda (Júpiter):
```js
function _paintJupiter(ctx, w, h, seed) {
  const bands = [/* tons laranja/marrom/creme baseados no seed */]
  bands.forEach(({y, height, color}) => {
    ctx.fillStyle = color
    ctx.fillRect(0, y, w, height)
  })
  // grande mancha: elipse escura deslocada pelo seed
  ctx.fillStyle = 'rgba(180,60,20,.6)'
  ctx.beginPath(); ctx.ellipse(w*(.4+seed*.2), h*.55, w*.12, h*.08, 0, 0, Math.PI*2)
  ctx.fill()
}
```

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

Regra geral: `SphereGeometry` + `MeshPhongMaterial({map: canvasTexture})`.
A textura canvas imita a fotografia real do corpo astronômico correspondente.
A esfera gira no eixo Y — velocidade proporcional à atividade do repo.

### ⚡ Estrela de Nêutrons (`estrela-de-neutrons`) → visual: Pulsar

- **Geometria**: `IcosahedronGeometry(r, 2)` — facetado, compacto
- **Textura**: branco-azulado sólido com emissividade alta, sem mapa de textura
- **Efeito extra**: dois arcos magnéticos (`TubeGeometry` sobre curva Bezier) girando nos eixos X e Z
- **Animação**: pulso de emissividade rápido (2 Hz) + rotação muito rápida (período 4s)

### 🌀 Gigante Gasoso (`gigante-gasoso`) → visual: Júpiter

- **Geometria**: `SphereGeometry(r, 64, 32)`
- **Textura** `_paintJupiter()`: bandas horizontais laranja/marrom/creme; mancha vermelha elíptica deslocada pelo seed
- **Anéis**: `TorusGeometry` inclinado 5° para repos `magnitude >= 4` (tipo Saturno)
- **Tamanho**: range 12–22 unidades
- **Animação**: rotação rápida (período 8s) — Júpiter tem o dia mais curto do sistema solar

### 🪨 Planeta Rochoso ativo (`planeta-rochoso-quente`) → visual: Marte

- **Textura** `_paintMars()`: vermelho-ferrugem + manchas escuras de crateras + calotas polares brancas nos polos
- **Tamanho**: range 5–11 unidades
- **Animação**: rotação prograde (período 18s)

### 🌍 Planeta Rochoso temperado (`planeta-rochoso`) → visual: Terra

- **Textura** `_paintEarth()`: manchas azuis (oceano) + verdes/marrons (continentes) + branco nos polos
- **Camada extra**: segunda esfera `r*1.03`, textura de nuvens semi-transparente, gira mais devagar
- **Animação**: rotação prograde (período 22s)

### 🌑 Planeta Rochoso frio/dormente (`planeta-rochoso-frio`) → visual: Lua / Mercúrio

- **Textura** `_paintMoon()`: cinza variado + crateras circulares de impacto densas
- **Animação**: rotação muito lenta (período 40s), retrógrada se `daysSinceCommit > 365`

### 🔴 Anã Vermelha (`ana-vermelha`) → visual: Vênus

- **Textura** `_paintVenus()`: laranja-amarelado uniforme com camadas de névoa espessa (gradiente radial)
- **Animação**: retrógrada (sentido horário) — Vênus gira ao contrário, período 30s
- **Tamanho**: range 3–7 unidades

### 🌊 Planeta Oceano (`planeta-oceano`) → visual: Terra oceânica

- **Textura** `_paintOcean()`: predominância azul profundo + shimmer de reflexo solar (faixa clara no equador)
- **Camada extra**: nuvens finas como na Terra, porém mais esparsas
- **Animação**: rotação prograde média (período 20s)

### 🧊 Planeta Gelado (`planeta-gelado`) → visual: Urano

- **Textura** `_paintUranus()`: azul-esverdeado liso com gradiente suave polo-equador
- **Eixo de rotação**: inclinado ~90° no mesh (Urano orbita "deitado")
- **Efeito**: partículas de gelo esparsas ao redor
- **Animação**: rotação lenta (período 35s)

### 🌊 Planeta Gás Frio (`gigante-gelado`) → visual: Netuno

- **Textura** `_paintNeptune()`: azul profundo + banding sutil + mancha escura irregular
- **Animação**: rotação moderada (período 15s)

### 🌑 Lua (`lua`) → visual: Lua terrestre

- **Textura** `_paintMoon()`: igual ao rochoso frio — cinza craterado
- **Efeito extra**: trilha pontilhada na órbita
- **Posicionamento**: anel mais interno

### 🛸 Satélite Artificial (`satelite-artificial`) — sem textura orgânica

- **Geometria**: `OctahedronGeometry(r)` — diamante
- **Material**: `MeshStandardMaterial({metalness:.8, roughness:.2})` — metal polido, sem mapa
- **Efeito extra**: painéis solares (`BoxGeometry` achatado) bilaterais
- **Animação**: rotação período 6s

### 🌌 Nebulosa (`nebulosa`) — sem superfície sólida

- **Geometria**: `PointCloud` esférico com 300 partículas, sem mesh central
- **Cor**: baseada no cluster semântico
- **Animação**: expansão/contração lenta

### 💥 Supernova (`supernova`) → visual: Eta Carinae

- **Textura** `_paintSupernova()`: plasma laranja-vermelho caótico, manchas brancas quentes no centro
- **Efeito extra**: partículas divergindo do centro
- **Animação**: pulso muito rápido (1.5 Hz), rotação caótica

### 🎮 Planeta Toys (`planeta-toys`) — único sintético

- **Textura**: canvas atualizado a cada frame com hue-rotate — gradiente rosa→roxo→azul ciclando
- **Glow sprite**: raio 8×, cor acompanha o hue

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
