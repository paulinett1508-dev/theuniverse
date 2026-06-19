#!/usr/bin/env bash
# Deploy do Oráculo do Universo na Polaris
set -euo pipefail

POLARIS="root@2.25.163.125"
SSH_OPTS="-i ~/.ssh/id_ed25519_nexus_vps01 -p 49222"

echo "=== Espelhando theuniverse em /opt/theuniverse ==="
# [PENDENTE SOL] requer credencial de leitura do repo privado na Polaris
ssh $SSH_OPTS "$POLARIS" "
  if [ -d /opt/theuniverse/.git ]; then
    cd /opt/theuniverse && git pull --ff-only
  else
    git clone https://github.com/paulinett1508-dev/theuniverse.git /opt/theuniverse
  fi
"

echo "=== venv + deps ==="
ssh $SSH_OPTS "$POLARIS" "
  mkdir -p /opt/oraculo
  python3 -m venv /opt/oraculo/venv
  /opt/oraculo/venv/bin/pip install -q -r /opt/theuniverse/oraculo/requirements.txt
"

echo "=== systemd ==="
ssh $SSH_OPTS "$POLARIS" "
  cp /opt/theuniverse/oraculo/oraculo.service /etc/systemd/system/
  systemctl daemon-reload
  if [ -f /opt/oraculo/.env ]; then
    systemctl enable oraculo.service
    systemctl restart oraculo.service
    systemctl status oraculo.service --no-pager | head -10
  else
    echo 'AVISO: /opt/oraculo/.env ausente — serviço NÃO iniciado. Criar .env e: systemctl enable --now oraculo.service'
  fi
"
echo "=== Done ==="
