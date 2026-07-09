#!/usr/bin/env bash
set -euo pipefail

python_cmd="${PYTHON:-python3}"

if ! command -v "$python_cmd" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    python_cmd="python"
  else
    echo "Python 3.10 or newer is required. Install Python, then run this script again." >&2
    exit 1
  fi
fi

"$python_cmd" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
PY

echo "Creating virtual environment in .venv"
"$python_cmd" -m venv .venv

if [ -f ".venv/bin/python" ]; then
  venv_python=".venv/bin/python"
else
  venv_python=".venv/Scripts/python.exe"
fi

echo "Upgrading pip"
"$venv_python" -m pip install --upgrade pip

echo "Installing NTRM development dependencies"
"$venv_python" -m pip install -r requirements-dev.txt

echo "Running offline demo"
"$venv_python" run_demo.py

if [ -d "web_dashboard" ]; then
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    node_major="$(node -p "process.versions.node.split('.')[0]")"
    if [ "$node_major" -ge 20 ]; then
      echo "Installing dashboard dependencies"
      (cd web_dashboard && npm install)
    else
      echo "Skipping dashboard dependency install because Node.js 20 or newer is required. Current version: $(node --version)" >&2
    fi
  else
    echo "Skipping dashboard dependency install because Node.js/npm was not found. Install Node.js 20+ from https://nodejs.org/ to run the web dashboard." >&2
  fi
fi

cat <<'MSG'

Setup complete.

Next time, activate the environment with:
  source .venv/bin/activate

Run the Python demo with:
  python run_demo.py

Run the web dashboard with:
  bash run_dashboard.sh
MSG
