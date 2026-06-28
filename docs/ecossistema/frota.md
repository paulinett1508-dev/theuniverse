# A Frota — Estrelas do Universo

> Catálogo de governança das máquinas que sustentam o universo.
> **Sem IPs, sem credenciais.** Só nome, papel e região. O detalhe técnico vive no `nexus-labsobral` (infra real).

## Taxonomia

No cosmos, **servidor = estrela**: a fornalha que emite energia e sustenta a vida ao redor — exatamente o que uma máquina faz com os planetas (apps) que hospeda em deploy.

- ✨ **TheGod** = o humano (acima do sistema — visão suprema, cria e orquestra)
- ⭐ **Estrelas** = VPS e servers (sustentam os planetas em produção)
- 🪐 **Planetas** = repos
- 🛰️ **Satélites** = motores de IA locais (dentro dos planetas)

Resolve o conflito planeta↔servidor: planeta é a *obra* (repo); estrela é a *fornalha* que lhe dá energia.

## Estrelas do Espaço Profundo (VPS / nuvem)

| estrela | designação anterior | papel | hospeda |
|---|---|---|---|
| **Polaris** ⭐ | vps-universo / srv1323779.hstgr.cloud | a estrela-guia / vidente | Obi-Wan, antigravity, cartola (4 containers), hqplus (5 containers), traefik-ai1k — IP: 195.200.5.145 · conta: paulinett1508@gmail.com (Hostinger) |
| **Antares** ⭐ | Zion (sbr-vps-zion) | o coração — refúgio de produção | sistemas Sobral em prod |

## Aglomerado do Lab (servers internos — LAN)

| estrela | designação anterior | papel |
|---|---|---|
| **Atlas** ⭐ | labsrvfiles-213 | sustenta a memória — servidor de arquivos |
| **Mira** ⭐ | labsrvzabbix-216 | a observadora — monitoramento Zabbix |
| **Rigel** ⭐ | labsobral-214 | a forja — build / CI (compila e integra) |
| **Bellatrix** ⭐ | labsrv05-218 | a guardiã — banco de dados |
| **Vega** ⭐ | labtools01-150 | a vigia — monitoramento |

## Naves (substrato / infra-cósmica)

Não são corpos celestes — são o **chão onde as estrelas pousam**. A estrela pisa na nave; a nave não é a estrela.

| nave | host | papel | multi-inquilino |
|---|---|---|---|
| **Oráculo-VPS** 🛰️ | `nexus-vps01` · 2.25.163.125 · Hostinger KVM4 (4vCPU/16GB/200GB/Ubuntu 24.04/Boston-EUA) | control plane off-site · olho externo da infra · host do Hermes | ⭐ Hermes (Qdrant + Ollama) · 👁️ olho do Sheldon · 🛡️ Greenbone/OpenVAS (17 containers) · nexus-sentinela |

> Fonte de verdade: `amilcar-cortex/oraculo/no-oraculo-vps.md` (espelho legível ao Observatório)
> Canônico interno: `Amilcar-Constellation/territorio/vps-oraculo.md`
> Pauta que roda nesta nave: `Amilcar-Constellation#12`

---

## Fronteira

| corpo | designação anterior | papel |
|---|---|---|
| **Heliopausa** 🛡️ | pfsense | a borda defensiva — onde o vento solar encontra o espaço externo (firewall / roteamento) |

## Notas

- Nomes de estrelas reais escolhidos pelo significado: Polaris guia, Antares é "coração", Atlas sustenta, Mira ("a maravilhosa") observa.
- As designações anteriores (Obi-Wan/Zion = tema Matrix) ficam registradas — o universo honra sua própria história.
- Frota 100% mapeada (2026-06-19): Rigel/Bellatrix/Vega confirmados pelo Sol.
- Vega (monitoramento) e Mira (Zabbix) coexistem — vigílias distintas; detalhar a divisão de papéis quando relevante.
