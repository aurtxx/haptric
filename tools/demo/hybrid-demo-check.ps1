param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
)
$ErrorActionPreference = 'Stop'
$DemoRoot = Join-Path $RepoRoot '.demo-hybrid'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $RepoRoot 'backend\manage.py'
$Org = '11111111-1111-4111-8111-111111111111'
$ExpectedExam = '22222222-2222-4222-8222-222222222222'
$ExpectedStudent = '55555555-5555-4555-8555-555555555555'
foreach ($Node in @('lan','cloud')) {
    $Database = Join-Path $DemoRoot "$Node.sqlite3"
    if (-not (Test-Path -LiteralPath $Database)) { throw "Missing $Node database: $Database" }
    $env:DATABASE_NAME = $Database
    $env:DATABASE_ENGINE = 'django.db.backends.sqlite3'
    $env:HAPTRIC_SYNC_ORGANIZATION_ID = $Org
    $DisplayDatabase = $Database.Replace('\', '/')
    $code = "from exams.models import Organization, Student, Exam, ExamAssignment, SyncOutbox; import json; org=Organization.objects.filter(id='$Org').first(); print(json.dumps({'node':'$Node','db':'$DisplayDatabase','organizations':Organization.objects.count(),'students':Student.objects.count(),'exams':Exam.objects.count(),'assignments':ExamAssignment.objects.count(),'reference_ids_aligned':bool(org and Student.objects.filter(id='$ExpectedStudent',organization=org).exists() and Exam.objects.filter(id='$ExpectedExam',organization=org).exists()),'pending':SyncOutbox.objects.filter(delivery_status__in=['pending','failed']).count()}))"
    $output = & $Python $Manage shell -c $code
    if ($LASTEXITCODE -ne 0) { throw "Health check failed for $Node" }
    $jsonLine = $output | Where-Object { $_ -match '^\{' } | Select-Object -Last 1
    $check = $jsonLine | ConvertFrom-Json
    if (-not $check.reference_ids_aligned) { throw "Reference IDs are not aligned for $Node" }
}
Write-Host 'Hybrid demo check passed: separate LAN/Cloud SQLite databases and aligned reference data are present.' -ForegroundColor Green
