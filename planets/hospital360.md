# hospital360

| campo         | valor |
|---|---|
| url           | https://github.com/paulinett1508-dev/hospital360 |
| visibilidade  | privado |
| cinturão      | kuiper |
| cluster       | gov-publico |
| status        | **ativo** (0 dias sem commit) |
| linguagem     | PHP |
| tamanho       | 0 KB |
| issues        | 0 abertas |
| criado        | 2026-07-01 |
| ultimo-commit | 2026-07-01 |

## Descrição

Sistema de gestao hospitalar (HIS) para o SUS - PHP 8.2 + PostgreSQL 15. Atendimento, prontuario, farmacia, cirurgia, faturamento SUS (BPA/AIH/APAC), e-SUS PEC, RNDS.

## README (excerpt)

Cópia sanitizada "Hospital360_Afonso" — o repo usa `LEIA-ME.md` em vez de `README.md`, por isso o censo não extrai excerpt.


## Estrutura raiz

```
dirs : ajax, assets, classes, config, deploy, docs, imagens, includes, instalador, scripts, stream, tests
files: .env.example, .gitattributes, .gitignore, .htaccess, ANALISE_PROJETO_HOSPITAL360.md, GUIA_INSTALACAO_DEBIAN.md, LEIA-ME.md, MANUAL_USUARIO.md, _tmp_build_doc.py, abrir-hospital360.ps1, agenda_ambulatorial.php, agenda_visual.php, aih.php, alta.php, apac.php, atendimento.php, backup.php, bpa.php, build.ps1, bula_arquivo.php, cadastros.php, cidadao.php, cirurgia.php, cirurgia_descricao.php, cirurgia_sala.php, cnes.php, cnes_vinculos.php, conexao_pec.php, config_painel_chamada.php, configuracoes.php, configurar-nginx-ssl.cmd, configurar-nginx-ssl.ps1, consulta.php, contexto_operacional.php, dashboard_executivo.php, deploy_logo.py, documento_digital_download.php, documentos.php, download_transferencia_anexo.php, emergencia.php, emergencia_triagem.php, enfermagem.php, escala_operacional.php, estoque.php, exame_grade.php, exame_resultado.php, exames.php, exportador_sus.php, farmacia.php, faturamento_sus.php, ficha_atendimento.php, fila_ambulatorial.php, fila_medica.php, fix_accents.ps1, fix_servidor.py, gestao_documental.php, h360-bench-demo.sql, h360-bench.sh, health.php, historico.php, home.php, homologacao.php, hot-restart.cmd, hot-restart.ps1, importar_pec_medicamentos.php, imprimir_atendimento.php, index.php, iniciar-local.ps1, iniciar.cmd, iniciar.ps1, install.sh, internacao.php, licenca.php, linha_tempo_paciente.php, login.php, logout.php, medicamentos.php, menu_admin.php, mostrar-resumo-instalacao.ps1, observacao.php, paciente.php, package-lock.json, package.json, painel_chamada.php, painel_hospitalar.php, parar.cmd, parar.ps1, playwright.config.ts, prescricao.php, profissionais.php, prontuario.php, regulacao_transferencia.php, relatorios.php, resetar-admin.ps1, resumo_alta.php, rnds_config.php, router.php, servico-hospital360.ps1, sigtap_import.php, solicitacoes_ambulatoriais.php, terminal_senhas.php, triagem.php, trocar_senha.php, usuario.php, validar_documento.php
```

## Notas do guardião

<!-- observações, alertas, dependências cruzadas -->

**Planeta legado em handover (2026-07-01).** Sistema herdado de outro dev (**cezar-fournier**, repo original `cezar-fournier/hospital360_php` @ `hospital360-php-v1.1`) que abandonou o projeto; handover amigável em andamento. Roda 100% em produção em municípios-clientes (parque instalado ainda não inventariado).

- **Este repo é a cópia sanitizada** ("Hospital360_Afonso"): sem histórico git original, sem `.env` real, sem chave privada de licenciamento Ed25519, sem suíte E2E, sem dados de paciente. Clone local: `corpos/kuiper/gov-publico/Hospital360`.
- **Amarras críticas**: (1) auto-update das instalações em produção ainda aponta pro GitHub do dev original (`HOSPITAL360_GITHUB_REPO` no `.env` de cada servidor); (2) chave privada de licenças ficou com ele — sem ela não se emite/renova licença; recomendação: regenerar par de chaves no primeiro release próprio; (3) schema híbrido — baseline em `config/assistencial.php` (266 KB), migrations só incrementais.
- **Riscos de segurança top** (auditoria 2026-07-01): login aceita hash legado MD5/SHA1/texto-puro (`login.php:59-72`); sem 2FA; CPF/CNS sem criptografia em repouso; trilha LGPD de prontuário incompleta (historico/linha_tempo/atendimento sem log de acesso).
- **Qualidade geral acima da média**: PDO prepared universal (sem SQLi encontrada), CSRF timing-safe, sessão única server-side, fail2ban+UFW+backups cifrados no install.sh, licenciamento Ed25519 com revogação remota.
- Dossiê completo da sessão 2026-07-01 na memória do guardião (`project_hospital360.md`). Checklist de handover com o dev original entregue na mesma sessão.
