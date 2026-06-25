---
description: Retomada robusta de sessão — reconstrói contexto completo em < 60s. Substitui /newsession.
---

Invocar skill `/abrirsessao` do agnostic-core com as seguintes adaptações do theuniverse:

**Hora real:**
```bash
date
ssh vps "TZ='America/Sao_Paulo' date"
```

**Git pull:**
```bash
git pull && git log --oneline -5 && git status
```

**Issues agendadas:**
```bash
gh issue list --label scheduled --state open
```

**Alertas do Observatório:**
```bash
gh issue list --label observatory-alert --state open
gh issue list --label observatory --state open
```

**Backlog:**
```bash
gh issue list --state open --limit 30
```

**Handoff mais recente:** ler o arquivo mais novo em `docs/handoffs/`.

**Memórias:** ler `C:\Users\pmiranda\.claude\projects\D--theuniverse\memory\MEMORY.md`.

**Status de serviços (Polaris):**
```bash
ssh vps "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```
Containers esperados: obi-wan, antigravity, b2-webhook-notifier, traefik (+ hqplus stack).

**Saída:**
```
SESSÃO RETOMADA — <data/hora real>

ONDE PARAMOS
<2-3 linhas do handoff verificadas vs. produção>

ISSUES PRIORITÁRIAS
- [scheduled] #N título — VENCIDA (Quando: ...)
- [blocked] #N — bloqueador: ...
- #N, #N, #N — próximas

GUARD-RAILS ATIVOS
- <o que NÃO fazer e por quê>

PRÓXIMA AÇÃO PROPOSTA
<ação específica — anunciar e aguardar "sim" se tocar infra>
```

**Regras invioláveis:**
- `observatory-alert` aberto → relatar antes de tudo, sem exceção
- Git pull antes de qualquer edição
- Handoff é ponto de partida — verificar estado real antes de agir em guard-rails
- Saída é briefing, não autorização: propor, aguardar "sim"
