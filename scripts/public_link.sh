#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"

if ! command -v npx >/dev/null 2>&1; then
  echo "Erro: npx não encontrado. Instale Node.js para gerar link público."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/dev/null

python app.py > /tmp/suinogest-app.log 2>&1 &
APP_PID=$!

cleanup() {
  kill "$APP_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2

echo "App local: http://127.0.0.1:${PORT}"

echo "Gerando link público..."
TUNNEL_PASSWORD="$(curl -fsS https://loca.lt/mytunnelpassword || true)"
if [ -n "$TUNNEL_PASSWORD" ]; then
  echo "Senha do túnel (se pedir password no celular): ${TUNNEL_PASSWORD}"
fi

npx --yes localtunnel --port "${PORT}"
