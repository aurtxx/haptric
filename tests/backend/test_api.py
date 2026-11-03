from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from exams.models import Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Student, User


@pytest.fixture
def tenant_fixture():
    org = Organization.objects.create(name="Harbor", slug="harbor")
    other_org = Organization.objects.create(name="Other", slug="other")
    admin = User.objects.create_user(username="admin", password="pw", organization=org, role=User.Roles.ADMIN)
    student_user = User.objects.create_user(username="student", password="pw", organization=org, role=User.Roles.STUDENT)
    other_admin = User.objects.create_user(username="other-admin", password="pw", organization=other_org, role=User.Roles.ADMIN)
    student = Student.objects.create(organization=org, user=student_user, name="Maya", student_id="MAYA-1")
    exam = Exam.objects.create(organization=org, created_by=admin, title="Foundations", duration_minutes=10, status=Exam.Status.PUBLISHED)
    section = ExamSection.objects.create(exam=exam, name="Core", position=1)
    question = Question.objects.create(organization=org, created_by=admin, question_type="single", prompt="Choose", options=["A", "B"], correct_answer="A", positive_marks=3, negative_marks=1)
    ExamQuestion.objects.create(section=section, question=question, position=1)
    ExamAssignment.objects.create(exam=exam, student=student)
    return locals()


@pytest.mark.django_db
def test_health_route_and_tenant_scoping(tenant_fixture):
    client = APIClient()
    assert client.get("/health/").status_code == 200
    client.force_authenticate(tenant_fixture["other_admin"])
    response = client.get("/api/v1/exams/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_student_exam_does_not_expose_answer_key(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["student_user"])
    response = client.get(f"/api/v1/exams/{tenant_fixture['exam'].id}/")
    assert response.status_code == 200
    question_payload = response.json()["sections"][0]["exam_questions"][0]["question"]
    assert "correct_answer" not in question_payload


@pytest.mark.django_db
def test_attempt_start_answer_and_idempotent_submit(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["student_user"])
    start = client.post("/api/v1/attempts/start/", {"exam": str(tenant_fixture["exam"].id)}, format="json", HTTP_IDEMPOTENCY_KEY="start-1")
    assert start.status_code == 201
    attempt_id = start.json()["id"]
    answer = client.put(f"/api/v1/attempts/{attempt_id}/answer/", {"question": str(tenant_fixture["question"].id), "value": "A"}, format="json")
    assert answer.status_code == 200
    submitted = client.post(f"/api/v1/attempts/{attempt_id}/submit/", {}, format="json")
    assert submitted.status_code == 200
    assert Decimal(submitted.json()["score"]) == Decimal("3.00")
    repeated = client.post(f"/api/v1/attempts/{attempt_id}/submit/", {}, format="json")
    assert repeated.status_code == 200
    assert repeated.json()["score"] == submitted.json()["score"]


@pytest.mark.django_db
def test_schedule_window_blocks_early_start(tenant_fixture):
    tenant_fixture["exam"].available_from = timezone.now() + timedelta(minutes=5)
    tenant_fixture["exam"].save(update_fields=["available_from"])
    client = APIClient()
    client.force_authenticate(tenant_fixture["student_user"])
    response = client.post("/api/v1/attempts/start/", {"exam": str(tenant_fixture["exam"].id)}, format="json")
    assert response.status_code == 409


@pytest.mark.django_db
def test_sync_push_is_idempotent_and_tenant_bound(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    event = {"idempotency_key": "sync-1", "event_type": "student.updated", "entity_type": "student", "entity_id": "s1", "payload": {"revision": 1}}
    first = client.post("/api/v1/sync/push/", {"events": [event]}, format="json")
    second = client.post("/api/v1/sync/push/", {"events": [event]}, format="json")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    client.force_authenticate(tenant_fixture["other_admin"])
    conflict = client.post("/api/v1/sync/push/", {"events": [event]}, format="json")
    assert conflict.status_code == 409


@pytest.mark.django_db
def test_csrf_session_login_and_me(tenant_fixture):
    client = APIClient(enforce_csrf_checks=True)
    csrf_response = client.get("/api/v1/auth/csrf/")
    assert csrf_response.status_code == 200
    token = csrf_response.json()["csrfToken"]
    response = client.post("/api/v1/auth/login/", {"username": "admin", "password": "pw"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    me_response = client.get("/api/v1/me/")
    assert me_response.status_code == 200
