param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
)
$ErrorActionPreference = 'Stop'
$DemoRoot = Join-Path $RepoRoot '.demo-hybrid'
$Database = Join-Path $DemoRoot 'lan.sqlite3'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $RepoRoot 'backend\manage.py'
if (-not (Test-Path -LiteralPath $Database)) { throw 'LAN database not found.' }
if ([string]::IsNullOrWhiteSpace($env:HAPTRIC_SYNC_TOKEN)) { throw 'Set HAPTRIC_SYNC_TOKEN in this terminal.' }
$env:DATABASE_NAME = $Database
$env:DATABASE_ENGINE = 'django.db.backends.sqlite3'
$env:HAPTRIC_NODE_ID = if ($env:HAPTRIC_NODE_ID) { $env:HAPTRIC_NODE_ID } else { 'lan-demo-node' }
$env:HAPTRIC_NODE_ROLE = 'lan'
$env:HAPTRIC_SYNC_ORGANIZATION_ID = '11111111-1111-4111-8111-111111111111'
$env:HAPTRIC_SYNC_URL = if ($env:HAPTRIC_SYNC_URL) { $env:HAPTRIC_SYNC_URL } else { 'http://127.0.0.1:8001/api/v1/sync/push/' }
& $Python $Manage sync_upstream
if ($LASTEXITCODE -ne 0) { throw 'Sync command failed.' }
