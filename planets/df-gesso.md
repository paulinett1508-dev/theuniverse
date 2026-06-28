# df-gesso

| campo         | valor |
|---|---|
| url           | https://github.com/paulinett1508-dev/df-gesso |
| visibilidade  | privado |
| cinturão      | pessoal |
| cluster       | produtos |
| status        | **ativo** (0 dias sem commit) |
| linguagem     | TypeScript |
| tamanho       | 0 KB |
| issues        | 0 abertas |
| criado        | 2026-06-28 |
| ultimo-commit | 2026-06-28 |

## Descrição

Site institucional + plataforma de vendas e fidelização para a DF Gesso — empresa de materiais e serviços de gesso. Vai além do modelo institucional tradicional: calculadora de materiais, catálogo completo de serviços, programa de fidelidade (DF Pontos) e área do cliente.

## Stack

| camada | tecnologia |
|---|---|
| framework | Next.js 15 (App Router) |
| estilo | Tailwind CSS |
| domínio | Hostinger |
| produção | Polaris VPS — Docker + Nginx + Traefik |
| preview/visual | Vercel — staging para validação rápida e revisão do designer |
| DB (F2+) | PostgreSQL via Neon ou container na Polaris |
| auth (F2+) | NextAuth.js |
| app (F5) | PWA sobre Next.js ou React Native |

## Identidade visual

Fornecida por designer externo — logo, paleta de cores e guia de estilo já existem. Não é escopo do dev. Integrar assets conforme entregues.

## Roadmap

| fase | escopo | status |
|---|---|---|
| F1 | Site institucional + catálogo completo de serviços + calculadora de materiais | 🔵 kickoff |
| F2 | Área do cliente: saldo de pontos · histórico de compras · pedidos · NF · boletos · promoções | ⏳ planejada |
| F3 | Programa DF Pontos: R$1 = 1pt · níveis Bronze/Prata/Ouro/Diamante · catálogo de recompensas | ⏳ planejada |
| F4 | Rastreamento de pedidos em tempo real | ⏳ planejada |
| F5 | Aplicativo próprio da DF Gesso | ⏳ planejada |

## Calculadora de Materiais (F1 — core feature)

Três modos:
- **Parede de bloco de gesso**: blocos + gesso cola + sisal
- **Forro de gesso**: placas + arame galvanizado + sisal + gesso acabamento
- **Divisórias**: quantidade + peso total + valor estimado

CTA: botão "Solicitar orçamento" → WhatsApp.

## Programa DF Pontos (F3)

| métrica | valor |
|---|---|
| acúmulo | R$ 1,00 = 1 ponto |
| bronze | até 50.000 pts |
| prata | 50.001 – 150.000 pts |
| ouro | 150.001 – 500.000 pts |
| diamante | acima de 500.000 pts |

Recompensas: camisa (10k) → boné+camisa (25k) → kit ferramentas (50k) → vale R$100 (100k) → vale R$300 (250k) → ferramenta profissional (500k) → prêmio especial anual (1M).

## Catálogo de Serviços (F1 — completo)

Todos os serviços prestados pela DF Gesso, não só os mais procurados:
- Forro de gesso (placas e molduras)
- Parede de bloco de gesso
- Divisórias de gesso
- Reboco com gesso (grosseiro)
- Acabamento e decoração em gesso

## Segurança e compliance

- Repo privado — assets de identidade visual nunca em repositório público
- Variáveis sensíveis via Vercel env vars (nunca em `.env` commitado)
- `.env.example` documentado sem valores reais
- NextAuth com provedores seguros na Fase 2
- Rate limiting nas APIs de orçamento/WhatsApp para evitar spam

## Dependências externas

- WhatsApp Business do cliente (link para orçamento via CTA)
- Designer externo: entrega logo + paleta + guia de estilo
- Neon (DB serverless) — ativado na Fase 2

## Notas do guardião

- Cliente tem recorrência estabelecida e PDF de proposta completo (2026-06-27)
- Identidade visual pronta — aguarda entrega dos assets pelo designer
- Parceiro/intermediário mencionou interesse em modelar custo da parceria (áudio 2026-06-27 17h)
- Escopo cresce em 5 fases; cluster `produtos` desde o início evita reclassificação futura
- Projeto pessoal do TheGod — fora da órbita institucional do Lab Sobral
