#!/usr/bin/env bash
set -euo pipefail

for f in /tmp/suinogest-app.pid /tmp/suinogest-tunnel.pid; do
  if [ -f "$f" ]; then
    PID="$(cat "$f")"
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID" || true
      echo "Processo $PID encerrado."
    fi
    rm -f "$f"
  fi
done

echo "Link público e app finalizados."
