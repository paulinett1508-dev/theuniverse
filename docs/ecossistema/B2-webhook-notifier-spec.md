# Subsistema B2 — Universe Webhook Notifier

> TheGod recebe notificação Telegram em tempo real de cada commit e PR em qualquer
> dos 31 planetas do universo observável.

---

## Arquitetura

```
GitHub (push/PR event)
  │  HMAC-SHA256 secret
  ▼
Polaris :9120  ──  webhook/receiver.py (FastAPI/uvicorn)
  │  httpx
  ▼
Telegram Bot (@guardiao_universo_bot)
  │
  ▼
TheGod
```

---

## Componentes

| arquivo | função |
|---|---|
| `webhook/receiver.py` | FastAPI — recebe evento, valida HMAC, formata, manda Telegram |
| `webhook/requirements.txt` | fastapi + uvicorn + httpx + python-dotenv |
| `webhook/webhook.service` | systemd unit (porta 9120, EnvironmentFile=/opt/obi-wan/.env) |
| `webhook/deploy.sh` | deploy na Polaris: pull → venv → firewall → systemd |
| `scripts/setup-webhooks.py` | registra webhook nos 31 repos via GitHub API |

---

## Variáveis de ambiente (em `/opt/obi-wan/.env`)

| variável | descrição |
|---|---|
| `TELEGRAM_TOKEN` | já existente (obi-wan) |
| `SOL_CHAT_ID` | já existente (obi-wan) |
| `WEBHOOK_SECRET` | HMAC secret — gerado na instalação, em `.vault` local |

---

## Eventos monitorados

| evento GitHub | quando |
|---|---|
| `push` | qualquer commit em qualquer branch (exceto tags e pushes vazios) |
| `pull_request` | opened · closed (merged) · closed (sem merge) · reopened |

---

## Formato das notificações

**Push (1 commit):**
```
🚀 sbrgestao  ·  main
👤 paulinett-miranda
📝 feat: adiciona módulo de relatórios
ver commit
```

**Push (N commits):**
```
🚀 sbrgestao  ·  feature/auth  (3 commits)
👤 paulinett-miranda
  · feat: OAuth provider
  · fix: redirect URI
  · chore: env var
ver diff
```

**PR aberto:**
```
🔀 tokentown  PR #12 aberto
👤 paulinett-miranda:  Adiciona autenticação OAuth
feature/oauth → main
ver PR
```

**PR mergeado:**
```
✅ tokentown  PR #12 mergeado por paulinett-miranda
Adiciona autenticação OAuth
ver PR
```

---

## Deploy

```bash
# 1. adicionar WEBHOOK_SECRET ao .env da Polaris
ssh -i ~/.ssh/vscode_key root@195.200.5.145 \
  "echo 'WEBHOOK_SECRET=<secret>' >> /opt/obi-wan/.env"

# 2. deploy do serviço
bash webhook/deploy.sh

# 3. registrar webhooks nos 31 repos
python scripts/setup-webhooks.py --dry-run   # confere primeiro
python scripts/setup-webhooks.py             # registra
```

---

## Segurança

- Toda requisição validada via HMAC-SHA256 (`X-Hub-Signature-256`)
- Secret nunca no git — vive em `.vault` (local) e `/opt/obi-wan/.env` (Polaris)
- Porta 9120 aberta só para GitHub webhook IPs (ver subsistema C futuro)

---

## Operação

```bash
# logs
journalctl -u webhook -f

# status
systemctl status webhook

# re-deploy após mudança no receiver
cd /opt/theuniverse && git pull && systemctl restart webhook

# reconfigurar webhooks (ex: após adicionar novo repo)
python scripts/setup-webhooks.py
```
