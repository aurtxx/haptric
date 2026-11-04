param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
)
$ErrorActionPreference = 'Stop'
$ExpectedRoot = [IO.Path]::GetFullPath((Join-Path $RepoRoot '.demo-hybrid'))
$ResolvedRoot = (Resolve-Path $ExpectedRoot -ErrorAction SilentlyContinue).Path
if ($ResolvedRoot -and $ResolvedRoot.TrimEnd('\') -ne $ExpectedRoot.TrimEnd('\')) { throw "Refusing to reset unexpected path: $ResolvedRoot" }
if (-not $ResolvedRoot) { Write-Host 'No hybrid demo directory exists.'; exit 0 }
$Allowed = @((Join-Path $ExpectedRoot 'lan.sqlite3'), (Join-Path $ExpectedRoot 'cloud.sqlite3'))
Get-ChildItem -LiteralPath $ExpectedRoot -File | ForEach-Object {
    if ($Allowed -notcontains $_.FullName) { throw "Refusing to remove unexpected file: $($_.FullName)" }
}
foreach ($File in $Allowed) { if (Test-Path -LiteralPath $File) { Remove-Item -LiteralPath $File -Force } }
if (-not (Get-ChildItem -LiteralPath $ExpectedRoot -Force)) { Remove-Item -LiteralPath $ExpectedRoot -Force }
Write-Host 'Known disposable hybrid demo databases removed.' -ForegroundColor Yellow
