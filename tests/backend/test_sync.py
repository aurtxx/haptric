import json
import os
import uuid
from datetime import timedelta
from urllib.error import URLError
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from exams.models import Answer, Attempt, Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Result, Student, SyncOutbox, User


@pytest.fixture
def sync_fixture():
    org = Organization.objects.create(name="Sync School", slug="sync-school")
    admin = User.objects.create_user(username="sync-admin", password="pw", organization=org, role=User.Roles.ADMIN)
    student_user = User.objects.create_user(username="sync-student", password="pw", organization=org, role=User.Roles.STUDENT)
    student = Student.objects.create(organization=org, user=student_user, name="Sync Student", student_id="SYNC-1")
    exam = Exam.objects.create(organization=org, created_by=admin, title="Sync Exam", duration_minutes=10, status=Exam.Status.PUBLISHED)
    section = ExamSection.objects.create(exam=exam, name="Section", position=1)
    question = Question.objects.create(organization=org, created_by=admin, question_type=Question.Types.SINGLE, prompt="Pick A", options=["A", "B"], correct_answer="A", positive_marks=1, negative_marks=0)
    ExamQuestion.objects.create(section=section, question=question, position=1)
    ExamAssignment.objects.create(exam=exam, student=student)
    return locals()


@pytest.mark.django_db
def test_attempt_mutations_emit_safe_outbox_events(sync_fixture):
    client = APIClient()
    client.force_authenticate(sync_fixture["student_user"])
    start = client.post("/api/v1/attempts/start/", {"exam": str(sync_fixture["exam"].id)}, format="json", HTTP_IDEMPOTENCY_KEY="sync-start")
    attempt_id = start.json()["id"]
    client.put(f"/api/v1/attempts/{attempt_id}/answer/", {"question": str(sync_fixture["question"].id), "value": "A"}, format="json")
    client.post(f"/api/v1/attempts/{attempt_id}/submit/", {}, format="json")
    events = list(SyncOutbox.objects.filter(entity_id=attempt_id).order_by("created_at"))
    assert [event.event_type for event in events] == ["attempt.started", "answer.saved", "attempt.submitted"]
    assert all(event.origin_node for event in events)
    assert all("correct_answer" not in event.payload and "positive_marks" not in event.payload for event in events)


@pytest.mark.django_db
def test_node_ingest_materializes_and_replays_idempotently(sync_fixture):
    event_id = str(uuid.uuid4())
    attempt_id = str(uuid.uuid4())
    now = timezone.now()
    envelope = {
        "event_id": event_id,
        "event_type": "attempt.submitted",
        "organization_id": str(sync_fixture["org"].id),
        "origin_node": "lan-node",
        "aggregate_type": "attempt",
        "aggregate_id": attempt_id,
        "occurred_at": now.isoformat(),
        "schema_version": 1,
        "idempotency_key": f"attempt-submitted:{attempt_id}",
        "payload": {
            "attempt_id": attempt_id,
            "exam_id": str(sync_fixture["exam"].id),
            "student_id": str(sync_fixture["student"].id),
            "started_at": (now - timedelta(minutes=2)).isoformat(),
            "deadline_at": (now + timedelta(minutes=8)).isoformat(),
            "submitted_at": now.isoformat(),
            "answers": [{"question_id": str(sync_fixture["question"].id), "value": "A", "saved_at": now.isoformat()}],
            "score": "1.00",
            "correct_count": 1,
            "incorrect_count": 0,
            "unanswered_count": 0,
        },
    }
    started_envelope = {
        **envelope,
        "event_id": str(uuid.uuid4()),
        "event_type": "attempt.started",
        "idempotency_key": f"attempt-started:{attempt_id}",
        "payload": {
            "attempt_id": attempt_id,
            "exam_id": str(sync_fixture["exam"].id),
            "student_id": str(sync_fixture["student"].id),
            "started_at": (now - timedelta(minutes=2)).isoformat(),
            "deadline_at": (now + timedelta(minutes=8)).isoformat(),
        },
    }
    client = APIClient()
    with patch.dict(os.environ, {"HAPTRIC_SYNC_TOKEN": "test-sync-token", "HAPTRIC_SYNC_ORGANIZATION_ID": str(sync_fixture["org"].id), "HAPTRIC_NODE_ID": "cloud-node"}):
        unauthenticated = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [envelope]}, format="json")
        assert unauthenticated.status_code == 401
        first = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [started_envelope, envelope]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token")
        replay = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [started_envelope, envelope]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token")
        assert first.status_code == replay.status_code == 200, first.json()
        assert replay.json()["accepted_event_ids"] == first.json()["accepted_event_ids"]
        assert Attempt.objects.filter(id=attempt_id).count() == 1
        assert Answer.objects.filter(attempt_id=attempt_id).count() == 1
        assert Result.objects.filter(attempt_id=attempt_id).count() == 1
        changed = {**envelope, "payload": {**envelope["payload"], "score": "0.00"}}
        conflict = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [changed]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token")
        assert conflict.status_code == 200
        assert conflict.json()["conflicts"] == [event_id]

    client.force_authenticate(sync_fixture["admin"])
    assert client.get(f"/api/v1/attempts/{attempt_id}/review/").status_code == 200


@pytest.mark.django_db
def test_sync_command_retains_events_when_upstream_is_unavailable(sync_fixture):
    SyncOutbox.objects.create(
        organization=sync_fixture["org"], event_type="attempt.started", entity_type="attempt", entity_id=str(uuid.uuid4()),
        idempotency_key="pending-sync-event", payload={"attempt_id": str(uuid.uuid4())}, origin_node="lan-node",
    )
    with patch.dict(os.environ, {"HAPTRIC_SYNC_URL": "http://127.0.0.1:9/api/v1/sync/push/", "HAPTRIC_SYNC_TOKEN": "test-sync-token"}):
        call_command("sync_upstream")
    event = SyncOutbox.objects.get(idempotency_key="pending-sync-event")
    assert event.delivery_status == SyncOutbox.DeliveryStatus.FAILED
    assert event.attempts == 1


@pytest.mark.django_db
def test_sync_command_batches_each_organization_independently(sync_fixture):
    other = Organization.objects.create(name="Second School", slug="second-school")
    first_event = SyncOutbox.objects.create(organization=sync_fixture["org"], event_type="attempt.started", entity_type="attempt", entity_id=str(uuid.uuid4()), idempotency_key="org-one-event", payload={"attempt_id": str(uuid.uuid4())}, origin_node="lan-node")
    second_event = SyncOutbox.objects.create(organization=other, event_type="attempt.started", entity_type="attempt", entity_id=str(uuid.uuid4()), idempotency_key="org-two-event", payload={"attempt_id": str(uuid.uuid4())}, origin_node="lan-node")
    requests = []

    class FakeResponse:
        def __init__(self, body):
            self.body = body
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return self.body

    def fake_urlopen(request, timeout=5):
        body = json.loads(request.data.decode())
        requests.append(body)
        return FakeResponse(json.dumps({"accepted_event_ids": [event["event_id"] for event in body["events"]], "conflicts": []}).encode())

    with patch.dict(os.environ, {"HAPTRIC_SYNC_URL": "http://cloud.test/api/v1/sync/push/", "HAPTRIC_SYNC_TOKEN": "test-sync-token"}), patch("exams.management.commands.sync_upstream.urlopen", side_effect=fake_urlopen):
        call_command("sync_upstream")

    assert len(requests) == 2
    assert {request["organization_id"] for request in requests} == {str(sync_fixture["org"].id), str(other.id)}
    assert all(len(request["events"]) == 1 for request in requests)
    assert SyncOutbox.objects.get(id=first_event.id).delivery_status == SyncOutbox.DeliveryStatus.DELIVERED
    assert SyncOutbox.objects.get(id=second_event.id).delivery_status == SyncOutbox.DeliveryStatus.DELIVERED


@pytest.mark.django_db
def test_sync_failure_for_one_organization_does_not_block_another(sync_fixture):
    other = Organization.objects.create(name="Third School", slug="third-school")
    first_event = SyncOutbox.objects.create(organization=sync_fixture["org"], event_type="attempt.started", entity_type="attempt", entity_id=str(uuid.uuid4()), idempotency_key="org-fail-event", payload={"attempt_id": str(uuid.uuid4())}, origin_node="lan-node")
    second_event = SyncOutbox.objects.create(organization=other, event_type="attempt.started", entity_type="attempt", entity_id=str(uuid.uuid4()), idempotency_key="org-success-event", payload={"attempt_id": str(uuid.uuid4())}, origin_node="lan-node")

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({"accepted_event_ids": [str(second_event.id)], "conflicts": []}).encode()

    def fake_urlopen(request, timeout=5):
        body = json.loads(request.data.decode())
        if body["organization_id"] == str(sync_fixture["org"].id):
            raise URLError("simulated outage")
        return FakeResponse()

    with patch.dict(os.environ, {"HAPTRIC_SYNC_URL": "http://cloud.test/api/v1/sync/push/", "HAPTRIC_SYNC_TOKEN": "test-sync-token"}), patch("exams.management.commands.sync_upstream.urlopen", side_effect=fake_urlopen):
        call_command("sync_upstream")

    assert SyncOutbox.objects.get(id=first_event.id).delivery_status == SyncOutbox.DeliveryStatus.FAILED
    assert SyncOutbox.objects.get(id=second_event.id).delivery_status == SyncOutbox.DeliveryStatus.DELIVERED


@pytest.mark.django_db
def test_sync_rejects_future_schema_and_post_submit_mutation(sync_fixture):
    client = APIClient()
    with patch.dict(os.environ, {"HAPTRIC_SYNC_TOKEN": "test-sync-token", "HAPTRIC_SYNC_ORGANIZATION_ID": str(sync_fixture["org"].id), "HAPTRIC_NODE_ID": "cloud-node"}):
        future = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [{"schema_version": 2, "event_type": "attempt.started"}]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token")
        assert future.status_code == 400

        attempt_id = str(uuid.uuid4())
        now = timezone.now()
        started = {
            "event_id": str(uuid.uuid4()), "event_type": "attempt.started", "organization_id": str(sync_fixture["org"].id), "origin_node": "lan-node", "aggregate_type": "attempt", "aggregate_id": attempt_id, "occurred_at": now.isoformat(), "schema_version": 1, "idempotency_key": f"start:{attempt_id}",
            "payload": {"attempt_id": attempt_id, "exam_id": str(sync_fixture["exam"].id), "student_id": str(sync_fixture["student"].id), "started_at": (now - timedelta(minutes=1)).isoformat(), "deadline_at": (now + timedelta(minutes=9)).isoformat()},
        }
        submitted = {
            **started,
            "event_id": str(uuid.uuid4()), "event_type": "attempt.submitted", "idempotency_key": f"submit:{attempt_id}",
            "payload": {**started["payload"], "submitted_at": now.isoformat(), "answers": [{"question_id": str(sync_fixture["question"].id), "value": "A"}], "score": "1.00", "correct_count": 1, "incorrect_count": 0, "unanswered_count": 0},
        }
        assert client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [started, submitted]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token").status_code == 200
        late_answer = {**submitted, "event_id": str(uuid.uuid4()), "event_type": "answer.saved", "idempotency_key": f"late:{attempt_id}", "payload": {**started["payload"], "question_id": str(sync_fixture["question"].id), "value": "B"}}
        late = client.post("/api/v1/sync/push/", {"organization_id": str(sync_fixture["org"].id), "events": [late_answer]}, format="json", HTTP_X_HAPTRIC_SYNC_TOKEN="test-sync-token")
        assert late.status_code == 200
        assert late.json()["conflicts"] == [late_answer["event_id"]]
