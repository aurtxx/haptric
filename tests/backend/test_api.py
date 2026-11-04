from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import IntegrityError
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
    assert "positive_marks" not in question_payload
    assert "negative_marks" not in question_payload
    direct_question = client.get(f"/api/v1/questions/{tenant_fixture['question'].id}/")
    assert direct_question.status_code == 403


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
    assert response.json()["organization"] == str(tenant_fixture["org"].id)
    me_response = client.get("/api/v1/me/")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"


@pytest.mark.django_db
def test_anonymous_me_and_invalid_login_are_safe(tenant_fixture):
    client = APIClient(enforce_csrf_checks=True)
    csrf = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
    anonymous = client.get("/api/v1/me/")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "authentication_required"
    invalid = client.post("/api/v1/auth/login/", {"username": "admin", "password": "wrong"}, format="json", HTTP_X_CSRFTOKEN=csrf)
    assert invalid.status_code == 401
    assert invalid.json()["code"] == "authentication_failed"


@pytest.mark.django_db
def test_logout_requires_csrf_and_ends_session(tenant_fixture):
    client = APIClient(enforce_csrf_checks=True)
    csrf = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
    login_response = client.post("/api/v1/auth/login/", {"username": "admin", "password": "pw"}, format="json", HTTP_X_CSRFTOKEN=csrf)
    assert login_response.status_code == 200
    missing_csrf = client.post("/api/v1/auth/logout/", {}, format="json")
    assert missing_csrf.status_code == 403
    csrf_after_login = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
    logout_response = client.post("/api/v1/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=csrf_after_login)
    assert logout_response.status_code == 200
    assert client.get("/api/v1/me/").status_code == 401
    assert client.get("/api/v1/auth/logout/").status_code == 405


@pytest.mark.django_db
def test_student_provisioning_creates_hashed_linked_user(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    response = client.post("/api/v1/students/provision/", {"name": "New Student", "student_id": "NEW-1", "username": "new-student", "temporary_password": "Temporary-123!"}, format="json")
    assert response.status_code == 201
    student = Student.objects.get(student_id="NEW-1", organization=tenant_fixture["org"])
    assert student.user is not None
    assert student.user.role == User.Roles.STUDENT
    assert student.user.organization_id == tenant_fixture["org"].id
    assert student.user.check_password("Temporary-123!")
    assert student.user.password != "Temporary-123!"
    assert response.json()["username"] == "new-student"
    assert "temporary_password" not in response.json()


@pytest.mark.django_db
def test_student_provisioning_rejects_duplicates_and_rolls_back(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    duplicate_username = client.post("/api/v1/students/provision/", {"name": "Duplicate", "student_id": "NEW-2", "username": "admin", "temporary_password": "Temporary-123!"}, format="json")
    assert duplicate_username.status_code == 400
    assert not Student.objects.filter(student_id="NEW-2").exists()
    duplicate_student_id = client.post("/api/v1/students/provision/", {"name": "Duplicate", "student_id": "MAYA-1", "username": "new-student-2", "temporary_password": "Temporary-123!"}, format="json")
    assert duplicate_student_id.status_code == 400
    assert not User.objects.filter(username="new-student-2").exists()
    with patch("exams.views.Student.objects.create", side_effect=IntegrityError):
        failed = client.post("/api/v1/students/provision/", {"name": "Rollback", "student_id": "ROLLBACK-1", "username": "rollback-user", "temporary_password": "Temporary-123!"}, format="json")
    assert failed.status_code == 400
    assert not User.objects.filter(username="rollback-user").exists()
    assert not Student.objects.filter(student_id="ROLLBACK-1").exists()


@pytest.mark.django_db
def test_student_provisioning_is_tenant_scoped(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["other_admin"])
    response = client.post("/api/v1/students/provision/", {"name": "Other Student", "student_id": "OTHER-1", "username": "other-student", "temporary_password": "Temporary-123!"}, format="json")
    assert response.status_code == 201
    created = Student.objects.get(student_id="OTHER-1")
    assert created.organization_id == tenant_fixture["other_org"].id
    client.force_authenticate(tenant_fixture["admin"])
    assert client.get(f"/api/v1/students/{created.id}/").status_code == 404
    client.force_authenticate(tenant_fixture["student_user"])
    unauthorized = client.post("/api/v1/students/provision/", {"name": "Blocked", "student_id": "BLOCKED-1", "username": "blocked", "temporary_password": "Temporary-123!"}, format="json")
    assert unauthorized.status_code == 403


@pytest.mark.django_db
def test_exam_authoring_persistence_schedule_publish_and_assignment(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    invalid_duration = client.post("/api/v1/exams/", {"title": "Invalid", "duration_minutes": 0}, format="json")
    assert invalid_duration.status_code == 400
    invalid_schedule = client.post("/api/v1/exams/", {"title": "Invalid schedule", "duration_minutes": 10, "available_from": "2030-01-02T10:00:00Z", "available_until": "2030-01-02T09:00:00Z"}, format="json")
    assert invalid_schedule.status_code == 400
    created = client.post("/api/v1/exams/", {"title": "API Authoring Exam", "duration_minutes": 30, "available_from": "2030-01-02T09:00:00Z", "available_until": "2030-01-02T11:00:00Z"}, format="json")
    assert created.status_code == 201
    exam_id = created.json()["id"]
    section = client.post("/api/v1/sections/", {"exam": exam_id, "name": "Demo Section", "position": 1}, format="json")
    assert section.status_code == 201
    section_id = section.json()["id"]
    question_ids = []
    for index in range(3):
        question = client.post("/api/v1/questions/", {"question_type": "single", "prompt": f"Synthetic question {index + 1}", "options": ["A", "B"], "correct_answer": "A", "positive_marks": "1", "negative_marks": "0"}, format="json")
        assert question.status_code == 201
        question_ids.append(question.json()["id"])
        attached = client.post("/api/v1/exam-questions/", {"section": section_id, "question_id": question.json()["id"], "position": index + 1}, format="json")
        assert attached.status_code == 201
    reopened = client.get(f"/api/v1/exams/{exam_id}/")
    assert reopened.status_code == 200
    assert reopened.json()["title"] == "API Authoring Exam"
    assert reopened.json()["duration_minutes"] == 30
    assert len(reopened.json()["sections"][0]["exam_questions"]) == 3
    published = client.post(f"/api/v1/exams/{exam_id}/publish/", {}, format="json")
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assignment = client.post(f"/api/v1/exams/{exam_id}/assign/", {"student": str(tenant_fixture["student"].id)}, format="json")
    assert assignment.status_code == 201
    duplicate = client.post(f"/api/v1/exams/{exam_id}/assign/", {"student": str(tenant_fixture["student"].id)}, format="json")
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == assignment.json()["id"]
    assert ExamAssignment.objects.filter(exam_id=exam_id, student=tenant_fixture["student"]).count() == 1


@pytest.mark.django_db
def test_published_exam_content_and_question_keys_are_immutable(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    exam = tenant_fixture["exam"]
    question = tenant_fixture["question"]
    section = exam.sections.first()
    create_link = client.post("/api/v1/exam-questions/", {"section": str(section.id), "question_id": str(question.id), "position": 2}, format="json")
    assert create_link.status_code == 400
    existing_link = exam.sections.first().exam_questions.first()
    update_link = client.patch(f"/api/v1/exam-questions/{existing_link.id}/", {"position": 2}, format="json")
    assert update_link.status_code == 400
    delete_link = client.delete(f"/api/v1/exam-questions/{existing_link.id}/")
    assert delete_link.status_code == 400
    update_question = client.patch(f"/api/v1/questions/{question.id}/", {"prompt": "Changed"}, format="json")
    assert update_question.status_code == 400
    delete_question = client.delete(f"/api/v1/questions/{question.id}/")
    assert delete_question.status_code == 400
    update_exam = client.patch(f"/api/v1/exams/{exam.id}/", {"title": "Changed"}, format="json")
    assert update_exam.status_code == 400


@pytest.mark.django_db
def test_draft_exam_cannot_be_assigned_and_cross_tenant_question_cannot_attach(tenant_fixture):
    client = APIClient()
    client.force_authenticate(tenant_fixture["admin"])
    draft = Exam.objects.create(organization=tenant_fixture["org"], created_by=tenant_fixture["admin"], title="Draft", duration_minutes=10)
    denied_assignment = client.post(f"/api/v1/exams/{draft.id}/assign/", {"student": str(tenant_fixture["student"].id)}, format="json")
    assert denied_assignment.status_code == 409
    section = ExamSection.objects.create(exam=draft, name="Core", position=1)
    other_question = Question.objects.create(organization=tenant_fixture["other_org"], created_by=tenant_fixture["other_admin"], question_type="single", prompt="Other", options=["A"], correct_answer="A")
    cross_tenant = client.post("/api/v1/exam-questions/", {"section": str(section.id), "question_id": str(other_question.id), "position": 1}, format="json")
    assert cross_tenant.status_code in {400, 404}
    other_student_user = User.objects.create_user(username="other-student", password="pw", organization=tenant_fixture["other_org"], role=User.Roles.STUDENT)
    other_student = Student.objects.create(organization=tenant_fixture["other_org"], user=other_student_user, name="Other Student", student_id="OTHER-1")
    cross_tenant_assignment = client.post(f"/api/v1/exams/{tenant_fixture['exam'].id}/assign/", {"student": str(other_student.id)}, format="json")
    assert cross_tenant_assignment.status_code == 404
