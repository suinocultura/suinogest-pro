#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"
SUBDOMAIN="${SUBDOMAIN:-suinogest-$(date +%H%M%S)}"
APP_LOG="/tmp/suinogest-app.log"
TUNNEL_LOG="/tmp/suinogest-tunnel.log"
APP_PID_FILE="/tmp/suinogest-app.pid"
TUNNEL_PID_FILE="/tmp/suinogest-tunnel.pid"
PUBLIC_URL="https://${SUBDOMAIN}.localhost.run"

if ! command -v ssh >/dev/null 2>&1; then
  echo "Erro: ssh não encontrado."
  exit 1
fi

if ! command -v nc >/dev/null 2>&1; then
  echo "Erro: nc (netcat) não encontrado."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/dev/null

# Encerra instâncias anteriores (se existirem)
if [ -f "$APP_PID_FILE" ] && kill -0 "$(cat "$APP_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$APP_PID_FILE")" || true
fi
if [ -f "$TUNNEL_PID_FILE" ] && kill -0 "$(cat "$TUNNEL_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$TUNNEL_PID_FILE")" || true
fi

nohup python app.py > "$APP_LOG" 2>&1 &
APP_PID=$!
echo "$APP_PID" > "$APP_PID_FILE"

sleep 2
if ! kill -0 "$APP_PID" 2>/dev/null; then
  echo "Erro: app não subiu. Veja log: $APP_LOG"
  exit 1
fi

nohup ssh \
  -o "ProxyCommand=nc -X connect -x proxy:8080 %h %p" \
  -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=30 \
  -o ExitOnForwardFailure=yes \
  -N \
  -R "${SUBDOMAIN}:80:localhost:${PORT}" \
  nokey@localhost.run > "$TUNNEL_LOG" 2>&1 &

TUNNEL_PID=$!
echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

sleep 2
if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
  echo "Erro: túnel não iniciou. Veja log: $TUNNEL_LOG"
  exit 1
fi

READY=""
for _ in $(seq 1 20); do
  if curl -I -s "$PUBLIC_URL" | head -n 1 | rg -q "200|301|302"; then
    READY="yes"
    break
  fi
  sleep 1
done

if [ -z "$READY" ]; then
  echo "Aviso: túnel criado, mas a URL ainda não respondeu. Tente novamente em alguns segundos."
fi

echo "App local: http://127.0.0.1:${PORT}"
echo "Link público: ${PUBLIC_URL}"
echo "PID app: ${APP_PID} | PID túnel: ${TUNNEL_PID}"
echo "Para encerrar: ./scripts/stop_public_link.sh"
