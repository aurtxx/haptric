param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$DemoRoot = Join-Path $RepoRoot '.demo-hybrid'
$LanDb = Join-Path $DemoRoot 'lan.sqlite3'
$CloudDb = Join-Path $DemoRoot 'cloud.sqlite3'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $RepoRoot 'backend\manage.py'

if (-not (Test-Path -LiteralPath $Python)) { throw "Create .venv first: $Python" }
if (-not (Test-Path -LiteralPath $Manage)) { throw "Django manage.py not found: $Manage" }
New-Item -ItemType Directory -Path $DemoRoot -Force | Out-Null

function Invoke-Migrate([string]$DatabasePath) {
    $env:DATABASE_NAME = $DatabasePath
    $env:DATABASE_ENGINE = 'django.db.backends.sqlite3'
    & $Python $Manage migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw "Migration failed for $DatabasePath" }
}

Invoke-Migrate $LanDb
Invoke-Migrate $CloudDb
Write-Host "Hybrid demo databases ready:" -ForegroundColor Green
Write-Host "  LAN:   $LanDb"
Write-Host "  Cloud: $CloudDb"
Write-Host "Next: set HAPTRIC_DEMO_PASSWORD and run seed-hybrid-demo.ps1."
