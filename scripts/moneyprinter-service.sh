#!/usr/bin/env bash
# Start/stop/status for MoneyPrinterTurbo on fixed ports (no port hopping).
#   API  (FastAPI/uvicorn): 8080  — port comes from config.toml listen_port
#   WebUI (Streamlit):      8501
# PIDs and logs live in .run/ (gitignored). A port held by a process we did not
# start is reported, never killed.
#
# Usage: scripts/moneyprinter-service.sh {start|stop|restart|status} [api|webui|all]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT/.run"
PY="$ROOT/.venv/bin/python"
# WebUI binds to all interfaces (owner decision: network-wide access). The Settings
# dialog shows and can back up every API key, so reach is limited by ufw to the
# Residence 2 LAN + Tailscale. MPT_HOST=127.0.0.1 restricts it to this machine.
HOST="${MPT_HOST:-0.0.0.0}"
API_PORT=8080
WEBUI_PORT=8501
mkdir -p "$RUN_DIR"

port_of() { [ "$1" = api ] && echo "$API_PORT" || echo "$WEBUI_PORT"; }

is_running() { # svc
  local pidf="$RUN_DIR/$1.pid"
  [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null
}

port_owner() { # port -> pid or empty (free port must not trip set -e/pipefail)
  { ss -ltnpH "sport = :$1" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2; } || true
}

start_svc() { # svc
  local svc=$1 port; port=$(port_of "$svc")
  if is_running "$svc"; then echo "$svc already running (pid $(cat "$RUN_DIR/$svc.pid"), :$port)"; return 0; fi
  local owner; owner=$(port_owner "$port")
  if [ -n "$owner" ]; then
    echo "ERROR: :$port is held by pid $owner ($(ps -o comm= -p "$owner")) which this script did not start." >&2
    echo "       Inspect with: ss -ltnp 'sport = :$port'  — stop it yourself if it is stale." >&2
    return 1
  fi
  [ -x "$PY" ] || { echo "ERROR: $PY missing — run 'uv sync' first." >&2; return 1; }
  [ -f "$ROOT/config.toml" ] || python3 "$ROOT/scripts/sync-config-from-mapping.py"
  cd "$ROOT"
  export PYTHONPATH="$ROOT"
  if [ "$svc" = api ]; then
    nohup "$PY" main.py >"$RUN_DIR/api.log" 2>&1 &
  else
    nohup "$PY" -m streamlit run webui/Main.py \
      --server.address="$HOST" --server.port="$WEBUI_PORT" \
      --browser.gatherUsageStats=False --client.toolbarMode=minimal \
      --logger.hideWelcomeMessage=True --server.showEmailPrompt=False \
      --server.headless=True >"$RUN_DIR/webui.log" 2>&1 &
  fi
  echo $! >"$RUN_DIR/$svc.pid"
  echo "$svc started (pid $!, :$port, log .run/$svc.log)"
}

stop_svc() { # svc
  local svc=$1 pidf="$RUN_DIR/$1.pid"
  if ! is_running "$svc"; then echo "$svc not running"; rm -f "$pidf"; return 0; fi
  local pid; pid=$(cat "$pidf")
  kill -TERM "$pid"
  for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  kill -0 "$pid" 2>/dev/null && { echo "$svc ignored SIGTERM, sending SIGKILL"; kill -KILL "$pid"; }
  rm -f "$pidf"; echo "$svc stopped"
}

status_svc() { # svc
  local port; port=$(port_of "$1")
  if is_running "$1"; then echo "$1: running (pid $(cat "$RUN_DIR/$1.pid"), :$port)"
  else echo "$1: stopped (:$port owner: $(port_owner "$port" || true))"; fi
}

action=${1:-status}; target=${2:-all}
svcs=(api webui); [ "$target" != all ] && svcs=("$target")
for s in "${svcs[@]}"; do
  case "$action" in
    start) start_svc "$s" ;;
    stop) stop_svc "$s" ;;
    restart) stop_svc "$s"; start_svc "$s" ;;
    status) status_svc "$s" ;;
    *) echo "usage: $0 {start|stop|restart|status} [api|webui|all]"; exit 2 ;;
  esac
done
