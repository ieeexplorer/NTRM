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

cat <<'MSG'

Setup complete.

Next time, activate the environment with:
  source .venv/bin/activate

Then run:
  python run_demo.py
MSG
