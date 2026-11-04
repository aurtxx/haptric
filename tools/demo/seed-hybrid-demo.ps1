param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [Parameter(Mandatory = $false)][string]$DemoPassword = $env:HAPTRIC_DEMO_PASSWORD
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($DemoPassword)) { throw 'Set HAPTRIC_DEMO_PASSWORD for this disposable demo run; do not commit it.' }
$DemoRoot = Join-Path $RepoRoot '.demo-hybrid'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $RepoRoot 'backend\manage.py'
$Org = '11111111-1111-4111-8111-111111111111'
$Exam = '22222222-2222-4222-8222-222222222222'
$Section = '33333333-3333-4333-8333-333333333333'
$Question1 = '44444444-4444-4444-8444-444444444444'
$Question2 = '44444444-4444-4444-8444-444444444445'
$Question3 = '44444444-4444-4444-8444-444444444446'
$Student = '55555555-5555-4555-8555-555555555555'

function Invoke-Seed([string]$DatabasePath) {
    $env:DATABASE_NAME = $DatabasePath
    $env:DATABASE_ENGINE = 'django.db.backends.sqlite3'
    $env:HAPTRIC_DEMO_PASSWORD = $DemoPassword
    $code = @"
import uuid
import os
from exams.models import Organization, User, Student, Exam, ExamSection, Question, ExamQuestion, ExamAssignment
org = Organization.objects.get_or_create(id=uuid.UUID('$Org'), defaults={'name':'Haptric Hybrid Demo','slug':'haptric-hybrid-demo','mode':'lan'})[0]
demo_password = os.environ['HAPTRIC_DEMO_PASSWORD']
admin = User.objects.get_or_create(username='demo-staff', defaults={'organization':org,'role':User.Roles.ADMIN})[0]
admin.organization = org; admin.role = User.Roles.ADMIN; admin.set_password(demo_password); admin.save()
student_user = User.objects.get_or_create(username='demo-student', defaults={'organization':org,'role':User.Roles.STUDENT})[0]
student_user.organization = org; student_user.role = User.Roles.STUDENT; student_user.set_password(demo_password); student_user.save()
student = Student.objects.get_or_create(id=uuid.UUID('$Student'), defaults={'organization':org,'user':student_user,'name':'Hybrid Demo Student','student_id':'HYBRID-001'})[0]
exam = Exam.objects.get_or_create(id=uuid.UUID('$Exam'), defaults={'organization':org,'created_by':admin,'title':'Hybrid Demo Exam','duration_minutes':10,'status':Exam.Status.PUBLISHED})[0]
section = ExamSection.objects.get_or_create(id=uuid.UUID('$Section'), defaults={'exam':exam,'name':'Demo Section','position':1})[0]
questions = [('$Question1','Which option is correct?'),('$Question2','Which value is largest?'),('$Question3','Which statement is true?')]
for qid, prompt in questions:
    question = Question.objects.get_or_create(id=uuid.UUID(qid), defaults={'organization':org,'created_by':admin,'question_type':Question.Types.SINGLE,'prompt':prompt,'options':['A','B','C'],'correct_answer':'A','positive_marks':1,'negative_marks':0})[0]
    ExamQuestion.objects.get_or_create(section=section, question=question, defaults={'position':questions.index((qid,prompt))+1})
ExamAssignment.objects.get_or_create(exam=exam, student=student)
print('seeded')
"@
    & $Python $Manage shell -c $code
    if ($LASTEXITCODE -ne 0) { throw "Seed failed for $DatabasePath" }
}

foreach ($Database in @('lan.sqlite3','cloud.sqlite3')) {
    $path = Join-Path $DemoRoot $Database
    if (-not (Test-Path -LiteralPath $path)) { throw "Run setup-hybrid-demo.ps1 first: $path" }
    Invoke-Seed $path
}
Write-Host 'Synthetic LAN and Cloud reference data seeded.' -ForegroundColor Green
Write-Host 'Accounts: demo-staff and demo-student. Password supplied only through HAPTRIC_DEMO_PASSWORD.'
