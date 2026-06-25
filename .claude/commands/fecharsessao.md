---
description: Encerramento robusto de sessão — auditoria git, issues, handoff, memórias. Zero limbo.
---

Invocar skill `/fecharsessao` do agnostic-core com as seguintes adaptações do theuniverse:

### 1. Auditoria Git
```bash
git status && git diff --stat && git log --oneline origin/HEAD..HEAD
```
Arquivos não commitados → commitar agora. Commits locais → `git push`.

### 2. Fechar issues resolvidas nesta sessão
```bash
gh issue close <N> --comment "feito em <commit-hash>. <1 linha do que foi feito>"
```

### 3. Criar issues para pendências discutidas mas não implementadas
```bash
gh issue create \
  --title "[DOMÍNIO] título curto" \
  --label <task|feature|improvement|bug|blocked> \
  --body $'**O quê:** ...\n**Por quê:** ...\n**Done:** <critério verificável>'
```
Cross-repo: usar `--repo paulinett1508-dev/<repo>` — nunca criar no repo errado.

### 4. Issues agendadas (com janela de execução)
```bash
gh issue create --title "[DOMÍNIO] título" --label "scheduled" \
  --body $'**O quê:** ...\n**Quando:** YYYY-MM-DD HH:MM (America/Sao_Paulo)\n**Por quê:** ...\n**Done:** <critério>'
```

### 5. Handoff — gerar em `docs/handoffs/YYYY-MM-DD-HHh.md`

Estrutura obrigatória:
```markdown
# Handoff — YYYY-MM-DD HHhMM

## Estado em voo
<o que estava sendo feito — específico o suficiente para retomar sem contexto>

## Issues abertas relevantes
<#N + título das em progresso ou bloqueadas>

## Guard-rails ativos
<o que NÃO fazer na próxima sessão e por quê>

## Próxima ação recomendada
<ação exata — ex: "rodar bash scripts/bump-version.sh patch 'motivo' às 18h30">

## Decisões desta sessão
<decisões arquiteturais ou de negócio não óbvias no código>
```

### 6. Memórias — salvar contexto novo
Verificar se algo aprendido merece persistência em `C:\Users\pmiranda\.claude\projects\D--theuniverse\memory\`.

### 7. Verificações passivas (Polaris)
```bash
ssh vps "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```
Containers Down → registrar no handoff.

### 8. Versionamento (se houve deploy ou issue fechada)
```bash
bash scripts/bump-version.sh <patch|minor|major> "razão"
```

### 9. Confirmação final
```
SESSÃO ENCERRADA
- Commits pushed: <N>
- Issues fechadas: #X, #Y
- Issues criadas: #A, #B
- Handoff: docs/handoffs/YYYY-MM-DD-HHh.md
- Versão: vX.Y.Z
```

**Regras invioláveis:**
- Nunca sair com working tree suja
- Nunca sair com trabalho discutido sem issue correspondente
- Guard-rails no handoff são mais importantes que o estado em voo
