#!/usr/bin/env bash
# Deploy do Universe Webhook Receiver na Polaris
set -euo pipefail

POLARIS="root@195.200.5.145"
SSH_OPTS="-i ~/.ssh/vscode_key -p 22"

echo "=== Espelhando theuniverse em /opt/theuniverse ==="
ssh $SSH_OPTS "$POLARIS" "
  if [ -d /opt/theuniverse/.git ]; then
    cd /opt/theuniverse && git pull --ff-only
  else
    git clone https://github.com/paulinett1508-dev/theuniverse.git /opt/theuniverse
  fi
"

echo "=== venv + deps ==="
ssh $SSH_OPTS "$POLARIS" "
  mkdir -p /opt/webhook
  python3 -m venv /opt/webhook/venv
  /opt/webhook/venv/bin/pip install -q -r /opt/theuniverse/webhook/requirements.txt
"

echo "=== firewall: abre porta 9120 ==="
ssh $SSH_OPTS "$POLARIS" "ufw allow 9120/tcp && ufw status | grep 9120 || true"

echo "=== systemd ==="
ssh $SSH_OPTS "$POLARIS" "
  cp /opt/theuniverse/webhook/webhook.service /etc/systemd/system/
  systemctl daemon-reload
  if grep -q WEBHOOK_SECRET /opt/obi-wan/.env; then
    systemctl enable webhook.service
    systemctl restart webhook.service
    systemctl status webhook.service --no-pager | head -10
  else
    echo 'AVISO: WEBHOOK_SECRET ausente no .env — adicionar antes de iniciar:'
    echo '  echo WEBHOOK_SECRET=<secret> >> /opt/obi-wan/.env'
    echo '  systemctl enable --now webhook.service'
  fi
"

echo "=== health check ==="
sleep 2
ssh $SSH_OPTS "$POLARIS" "curl -sf http://localhost:9120/health && echo ' OK' || echo ' FALHOU'"

echo "=== Done ==="
echo ""
echo "Próximo passo: python scripts/setup-webhooks.py"
