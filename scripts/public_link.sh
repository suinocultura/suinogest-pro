#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"
APP_LOG="/tmp/suinogest-app.log"
TUNNEL_LOG="/tmp/suinogest-tunnel.log"
APP_PID_FILE="/tmp/suinogest-app.pid"
TUNNEL_PID_FILE="/tmp/suinogest-tunnel.pid"

if ! command -v npx >/dev/null 2>&1; then
  echo "Erro: npx não encontrado. Instale Node.js para gerar link público."
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

nohup npx --yes localtunnel --port "$PORT" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

URL=""
for _ in $(seq 1 30); do
  URL="$(sed -n 's/.*your url is: \(https:\/\/.*\)/\1/p' "$TUNNEL_LOG" | tail -n1)"
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

if [ -z "$URL" ]; then
  echo "Erro: não consegui obter URL do túnel. Veja log: $TUNNEL_LOG"
  exit 1
fi

TUNNEL_PASSWORD="$(curl -fsS https://loca.lt/mytunnelpassword || true)"

echo "App local: http://127.0.0.1:${PORT}"
echo "Link público: ${URL}"
if [ -n "$TUNNEL_PASSWORD" ]; then
  echo "Senha do túnel (se pedir password no celular): ${TUNNEL_PASSWORD}"
fi
echo "PID app: ${APP_PID} | PID túnel: ${TUNNEL_PID}"
echo "Para encerrar: ./scripts/stop_public_link.sh"
