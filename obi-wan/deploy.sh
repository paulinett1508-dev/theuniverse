#!/usr/bin/env bash
# Deploy do Obi-Wan na Polaris
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
  mkdir -p /opt/obi-wan
  python3 -m venv /opt/obi-wan/venv
  /opt/obi-wan/venv/bin/pip install -q -r /opt/theuniverse/obi-wan/requirements.txt
"

echo "=== systemd ==="
ssh $SSH_OPTS "$POLARIS" "
  cp /opt/theuniverse/obi-wan/obi-wan.service /etc/systemd/system/
  systemctl daemon-reload
  if [ -f /opt/obi-wan/.env ]; then
    systemctl enable obi-wan.service
    systemctl restart obi-wan.service
    systemctl status obi-wan.service --no-pager | head -10
  else
    echo 'AVISO: /opt/obi-wan/.env ausente — serviço NÃO iniciado. Criar .env e: systemctl enable --now obi-wan.service'
  fi
"
echo "=== Done ==="
