$ErrorActionPreference = "Stop"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Error "Python 3.10 or newer is required. Install Python from https://www.python.org/downloads/ and tick 'Add Python to PATH'."
}

if ($python.Name -eq "py.exe" -or $python.Name -eq "py") {
    $pythonExe = "py"
    $pythonArgs = @("-3")
} else {
    $pythonExe = $python.Source
    $pythonArgs = @()
}

& $pythonExe @pythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'Python 3.10 or newer is required.')"

Write-Host "Creating virtual environment in .venv"
& $pythonExe @pythonArgs -m venv .venv

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Upgrading pip"
& $venvPython -m pip install --upgrade pip

Write-Host "Installing NTRM development dependencies"
& $venvPython -m pip install -r requirements-dev.txt

Write-Host "Running offline demo"
& $venvPython run_demo.py

Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "Next time, activate the environment with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then run:"
Write-Host "  python run_demo.py"
