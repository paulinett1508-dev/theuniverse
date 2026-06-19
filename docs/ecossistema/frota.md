# A Frota — Estrelas do Universo

> Catálogo de governança das máquinas que sustentam o universo.
> **Sem IPs, sem credenciais.** Só nome, papel e região. O detalhe técnico vive no `nexus-labsobral` (infra real).

## Taxonomia

No cosmos, **servidor = estrela**: a fornalha que emite energia e sustenta a vida ao redor — exatamente o que uma máquina faz com os planetas (apps) que hospeda em deploy.

- ☀️ **Sol** = o humano (estrela central da consciência, decide)
- ⭐ **Estrelas** = VPS e servers (sustentam os planetas em produção)
- 🪐 **Planetas** = repos
- 🛰️ **Satélites** = motores de IA locais (dentro dos planetas)

Resolve o conflito planeta↔servidor: planeta é a *obra* (repo); estrela é a *fornalha* que lhe dá energia.

## Estrelas do Espaço Profundo (VPS / nuvem)

| estrela | designação anterior | papel | hospeda |
|---|---|---|---|
| **Polaris** ⭐ | Oráculo (nexus-vps01) | a estrela-guia / vidente | motor Hermes (RAG, MCP, oráculo) |
| **Antares** ⭐ | Zion (sbr-vps-zion) | o coração — refúgio de produção | sistemas Sobral em prod |
| **Sirius** ⭐ | VPS Hostinger | a mais brilhante (face pública) | SuperCartola (scm-prod) |

## Aglomerado do Lab (servers internos — LAN)

| estrela | designação anterior | papel |
|---|---|---|
| **Atlas** ⭐ | labsrvfiles-213 | sustenta a memória — servidor de arquivos |
| **Mira** ⭐ | labsrvzabbix-216 | a observadora — monitoramento Zabbix |
| **Rigel** ⭐ | labsobral-214 | a forja — build / CI (compila e integra) |
| **Bellatrix** ⭐ | labsrv05-218 | a guardiã — banco de dados |
| **Vega** ⭐ | labtools01-150 | a vigia — monitoramento |

## Fronteira

| corpo | designação anterior | papel |
|---|---|---|
| **Heliopausa** 🛡️ | pfsense | a borda defensiva — onde o vento solar encontra o espaço externo (firewall / roteamento) |

## Notas

- Nomes de estrelas reais escolhidos pelo significado: Polaris guia, Antares é "coração", Sirius é a mais brilhante, Atlas sustenta, Mira ("a maravilhosa") observa.
- As designações anteriores (Oráculo/Zion = tema Matrix) ficam registradas — o universo honra sua própria história.
- Frota 100% mapeada (2026-06-19): Rigel/Bellatrix/Vega confirmados pelo Sol.
- Vega (monitoramento) e Mira (Zabbix) coexistem — vigílias distintas; detalhar a divisão de papéis quando relevante.
