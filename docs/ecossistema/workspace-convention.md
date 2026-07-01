# Convenção de Workspace Local

> Resolve a issue #18. Define onde os planetas (repos) são clonados no filesystem local do TheGod.

## Decisão

`D:\theuniverse` é a raiz física oficial. Não existe mais "workspace solto" fora dela para
projetos privados.

Os clones vivem em `corpos/`, uma árvore separada da documentação do observatório
(`planets/`, `constellations/`, `docs/`) e **git-ignorada** — cada planeta é seu próprio
repo, com seu próprio `.git`, independente do git do theuniverse.

```
D:\theuniverse\
├── planets/          ← fichas (docs, rastreadas no git do theuniverse)
├── constellations/   ← manifestos (docs, rastreados)
└── corpos/           ← clones físicos (NÃO rastreado — .gitignore)
    └── <cinturão>/
        └── <cluster>/
            └── <planeta>/   ← clone real, com .git próprio
```

`<cinturão>` e `<cluster>` vêm direto do Censo (`scripts/censo.py`, dicts `NATUREZA` e
`CLUSTERS`) — a mesma classificação que já aparece em `planets/_index.md`. Nada é
inventado por fora: a árvore de pastas é um espelho físico do catálogo.

## Escopo: só Kuiper

`corpos/` materializa **só o cinturão Kuiper** (órbita privada/individual — os
planetas que estavam "soltos"). Gould e Van Allen (cinturões profissionais) têm local
de clone canônico **fora do theuniverse** — não são duplicados aqui, para não recriar
o problema original (dois clones do mesmo repo, sem saber qual é o "de verdade").

Para codar um planeta Kuiper: abrir direto `corpos/kuiper/<cluster>/<planeta>`.

## Gould / Van Allen — local canônico: `C:\AMILCAR-CONSTELATTION`

Raiz local da constelação Amilcar (repos `Amilcar-Constellation` e `matrix-core`, este
em transição de identidade). Não é organizada por cinturão/cluster do Censo — segue a
própria taxonomia por **tipo de corpo** já documentada em `constellations/amilcar.md`:

```
C:\AMILCAR-CONSTELATTION\
├── estrelas/     ← ⭐ hermes, nexus-labsobral, sbrgestao
├── planetas/     ← 🪐 CENTROCULTURALSBR, FinanceFlow, M365, m365-portal
├── satelites/    ← 🛰️ SbrChecks, SbrTask
├── cortex/       ← 🧠 amilcar-cortex (clone direto, contém especialistas/ferramentas)
├── dominios/     ← 🗺️ amilcar-dominios (monorepo departamental)
└── nucleo/       ← AMILCARCONSTELATTION, amilcar-core, mcp-eventos, sentinel-core
```

Cada subpasta é um clone real (`.git` próprio), igual ao padrão do `corpos/`. A raiz em
si não é um repo — é só o container do workspace (tem `.code-workspace` próprio).

Para codar um planeta Gould/Van Allen: abrir a pasta correspondente dentro dessa árvore,
não `corpos/`. `constellations/amilcar.md` é a fonte de verdade de qual corpo é qual.

## Ferramenta

`scripts/workspace.py` materializa a árvore automaticamente:

```bash
python scripts/workspace.py            # clona o que faltar (kuiper)
python scripts/workspace.py --dry-run  # só mostra o plano, não clona
```

Idempotente — só clona o que falta, nunca deleta, nunca sobrescreve. Token do `.vault`
é usado só no momento do `git clone` (via `x-access-token@`) e nunca fica gravado em
`.git/config` — o remote é reescrito para a URL limpa logo em seguida.

## Pendências

- **`temperodemamae`**: cinturão `nao-classificado` no Censo — não entra em `corpos/`
  até ser classificado.
