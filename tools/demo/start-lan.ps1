param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')),
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$DemoRoot = Join-Path $RepoRoot '.demo-hybrid'
$Database = Join-Path $DemoRoot 'lan.sqlite3'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $RepoRoot 'backend\manage.py'
if (-not (Test-Path -LiteralPath $Database)) { throw 'Run setup-hybrid-demo.ps1 and seed-hybrid-demo.ps1 first.' }
if ([string]::IsNullOrWhiteSpace($env:HAPTRIC_SYNC_TOKEN)) { throw 'Set HAPTRIC_SYNC_TOKEN in this terminal.' }
$env:DATABASE_NAME = $Database
$env:DATABASE_ENGINE = 'django.db.backends.sqlite3'
$env:HAPTRIC_NODE_ID = if ($env:HAPTRIC_NODE_ID) { $env:HAPTRIC_NODE_ID } else { 'lan-demo-node' }
$env:HAPTRIC_NODE_ROLE = 'lan'
$env:HAPTRIC_SYNC_ORGANIZATION_ID = '11111111-1111-4111-8111-111111111111'
$env:HAPTRIC_SYNC_URL = if ($env:HAPTRIC_SYNC_URL) { $env:HAPTRIC_SYNC_URL } else { 'http://127.0.0.1:8001/api/v1/sync/push/' }
$env:CORS_ALLOWED_ORIGINS = if ($env:CORS_ALLOWED_ORIGINS) { $env:CORS_ALLOWED_ORIGINS } else { 'http://127.0.0.1:5173' }
$env:CSRF_TRUSTED_ORIGINS = if ($env:CSRF_TRUSTED_ORIGINS) { $env:CSRF_TRUSTED_ORIGINS } else { 'http://127.0.0.1:5173' }
Write-Host "LAN node: $Database on http://127.0.0.1:$Port" -ForegroundColor Cyan
& $Python $Manage runserver "127.0.0.1:$Port" --noreload
