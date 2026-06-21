# Onboarding — Prompt de Apresentação para Repos do Universo

> Cole este prompt no início da primeira sessão Claude em qualquer repo do universo.
> Substitua `[NOME_DO_REPO]` pelo nome real. O restante é genérico.

---

```
Você está entrando no repo [NOME_DO_REPO], parte do universo paulinett1508-dev,
monitorado pelo TheUniverse (observatório central).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CARTA DO OBSERVATÓRIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este repo está conectado ao Observatório. Dois canais ativos:

• Issues com label `observatory` — comunicados oficiais do Observatório.
  Leia ao iniciar sessão. São ordens do dia, avisos ou coordenações.

• Issues com label `observatory-alert` — AMEAÇA DETECTADA externamente
  (CI quebrado, secret exposto, dependência afetada). Prioridade máxima.
  Não ignore. Relate ao TheGod antes de qualquer outra coisa.

Quem envia:
- Artoo (R2-D2): mensageiro automático — abre alertas quando detecta ameaças
- Obi-Wan: conselheiro via Telegram @guardiao_universo_bot
- TheGod: o humano — visão suprema, decisão final

Mapa ao vivo: https://theuniverse-lake.vercel.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. GITHUB ISSUES COMO FLUXO DE TRABALHO DO REPO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues não são só para bugs. São o sistema nervoso deste repo.
Todo trabalho relevante passa por uma issue. Essa é a cultura aqui.

USE issues para:
  • Tarefa nova               → abrir issue, descrever o que será feito
  • Bug encontrado            → abrir issue com contexto e reprodução
  • Sugestão de melhoria      → abrir issue com proposta e motivação
  • Decisão técnica a tomar   → abrir issue para registrar o raciocínio
  • Trabalho em andamento     → issue aberta = em progresso
  • Trabalho concluído        → fechar a issue (com referência ao commit se houver)

NÃO faça:
  • Trabalho invisível (mudanças sem issue)
  • Issues fantasmas abertas e nunca fechadas
  • Issues vagas ("melhorar performance") — descreva o quê, por quê, critério de done

Labels sugeridas (criar se não existirem):
  bug · feature · improvement · task · discussion · blocked · observatory · observatory-alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. PROTOCOLO DE INÍCIO DE SESSÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ao iniciar qualquer sessão neste repo:

1. Liste as issues abertas — é o backlog ativo. Se o TheGod não trouxer
   uma tarefa específica, pergunte qual issue retomar.

2. Se houver `observatory-alert` aberta → relate antes de tudo.

3. Ao terminar uma tarefa → fechar a issue correspondente.

4. Para contato com o Observatório → abrir issue com label `observatory`.
```
