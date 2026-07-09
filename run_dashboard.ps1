param(
    [int]$Port = 3000
)

$ErrorActionPreference = "Stop"

function Test-PortAvailable {
    param([int]$Candidate)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Candidate)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue

if (-not $node -or -not $npm) {
    Write-Host "Node.js 20 or newer with npm is required to run the web dashboard." -ForegroundColor Red
    Write-Host "Install the LTS version from https://nodejs.org/, reopen PowerShell, then run this script again."
    exit 1
}

$nodeMajor = [int](& node -p "process.versions.node.split('.')[0]")
if ($nodeMajor -lt 20) {
    Write-Host "Node.js 20 or newer is required. Current version: $(& node --version)" -ForegroundColor Red
    exit 1
}

$dashboardDir = Join-Path $PSScriptRoot "web_dashboard"
if (-not (Test-Path $dashboardDir)) {
    Write-Host "Cannot find the dashboard folder: $dashboardDir" -ForegroundColor Red
    exit 1
}

$chosenPort = $Port
while (-not (Test-PortAvailable $chosenPort)) {
    Write-Host "Port $chosenPort is busy; trying $($chosenPort + 1)."
    $chosenPort += 1
}

Push-Location $dashboardDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing dashboard dependencies..."
        npm install
    }

    Write-Host ""
    Write-Host "Starting NTRM Dashboard..."
    Write-Host "Open http://127.0.0.1:$chosenPort"
    Write-Host ""
    npm run dev -- --hostname 127.0.0.1 --port $chosenPort
} finally {
    Pop-Location
}
