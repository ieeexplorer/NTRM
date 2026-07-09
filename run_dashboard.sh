#!/usr/bin/env bash
set -euo pipefail

port="${1:-3000}"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js 20 or newer with npm is required to run the web dashboard." >&2
  echo "Install the LTS version from https://nodejs.org/, reopen your terminal, then run this script again." >&2
  exit 1
fi

node_major="$(node -p "process.versions.node.split('.')[0]")"
if [ "$node_major" -lt 20 ]; then
  echo "Node.js 20 or newer is required. Current version: $(node --version)" >&2
  exit 1
fi

is_port_free() {
  node -e "const net=require('net'); const port=Number(process.argv[1]); const s=net.createServer(); s.once('error',()=>process.exit(1)); s.listen(port,'127.0.0.1',()=>s.close(()=>process.exit(0)));" "$1"
}

while ! is_port_free "$port"; do
  echo "Port $port is busy; trying $((port + 1))."
  port="$((port + 1))"
done

cd "$(dirname "$0")/web_dashboard"

if [ ! -d node_modules ]; then
  echo "Installing dashboard dependencies..."
  npm install
fi

echo
echo "Starting NTRM Dashboard..."
echo "Open http://127.0.0.1:$port"
echo
npm run dev -- --hostname 127.0.0.1 --port "$port"
