from decimal import Decimal
import os
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Answer, AuditEvent, Attempt, Exam, ExamQuestion, Result, Student, SyncOutbox

SYNC_EVENT_TYPES = {"attempt.started", "answer.saved", "attempt.submitted"}


def sync_node_id():
    return os.getenv("HAPTRIC_NODE_ID", "local-node")


def create_sync_event(*, organization, event_type, entity_type, entity_id, payload, idempotency_key):
    """Create an immutable, traceable outbox envelope in the business transaction."""
    return SyncOutbox.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "organization": organization,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "payload": payload,
            "origin_node": sync_node_id(),
            "schema_version": 1,
            "occurred_at": timezone.now(),
        },
    )[0]


def _parse_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed


@transaction.atomic
def apply_sync_event(*, envelope, organization):
    """Apply one authenticated node event. Only the three supported event types are accepted."""
    event_id = envelope.get("event_id")
    event_type = envelope.get("event_type")
    payload = envelope.get("payload")
    if not event_id or event_type not in SYNC_EVENT_TYPES or not isinstance(payload, dict):
        raise ValueError("malformed_or_unsupported_event")
    if str(envelope.get("organization_id")) != str(organization.id):
        raise PermissionError("organization_mismatch")
    from uuid import UUID
    try:
        UUID(str(event_id))
    except ValueError as exc:
        raise ValueError("invalid_event_id") from exc
    existing = SyncOutbox.objects.filter(id=event_id).first()
    if existing:
        if existing.organization_id != organization.id or existing.event_type != event_type or existing.payload != payload:
            raise RuntimeError("event_conflict")
        return existing, False
    existing_key = SyncOutbox.objects.filter(idempotency_key=envelope.get("idempotency_key")).first()
    if existing_key:
        if existing_key.organization_id != organization.id or existing_key.id != event_id or existing_key.payload != payload:
            raise RuntimeError("event_conflict")
        return existing_key, False
    attempt_id = payload.get("attempt_id")
    if not attempt_id:
        raise ValueError("missing_attempt_id")
    if event_type == "attempt.started":
        exam = Exam.objects.get(id=payload["exam_id"], organization=organization)
        student = Student.objects.get(id=payload["student_id"], organization=organization)
        started_at = _parse_datetime(payload.get("started_at"))
        deadline_at = _parse_datetime(payload.get("deadline_at"))
        if not started_at or not deadline_at:
            raise ValueError("missing_attempt_timestamps")
        attempt, created = Attempt.objects.get_or_create(
            id=attempt_id,
            defaults={
                "exam": exam,
                "student": student,
                "status": Attempt.Status.IN_PROGRESS,
                "started_at": started_at,
                "deadline_at": deadline_at,
                "idempotency_key": f"synced:{attempt_id}",
            },
        )
        if not created and (
            str(attempt.exam_id) != str(exam.id)
            or str(attempt.student_id) != str(student.id)
            or attempt.started_at != started_at
            or attempt.deadline_at != deadline_at
        ):
            raise RuntimeError("event_conflict")
    elif event_type == "answer.saved":
        attempt = Attempt.objects.get(id=attempt_id, exam__organization=organization)
        question = ExamQuestion.objects.get(question_id=payload["question_id"], section__exam=attempt.exam).question
        try:
            validate_answer_value(question, payload.get("value"))
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        if attempt.status == Attempt.Status.SUBMITTED:
            existing_answer = Answer.objects.filter(attempt=attempt, question=question).first()
            if not existing_answer or existing_answer.value != payload.get("value"):
                raise RuntimeError("event_conflict")
        else:
            Answer.objects.update_or_create(attempt=attempt, question=question, defaults={"value": payload.get("value")})
    elif event_type == "attempt.submitted":
        attempt = Attempt.objects.get(id=attempt_id, exam__organization=organization)
        for answer in payload.get("answers", []):
            question = ExamQuestion.objects.get(question_id=answer["question_id"], section__exam=attempt.exam).question
            try:
                validate_answer_value(question, answer.get("value"))
            except ValidationError as exc:
                raise ValueError(str(exc)) from exc
            Answer.objects.update_or_create(attempt=attempt, question=question, defaults={"value": answer.get("value")})
        expected_score = Decimal("0")
        expected_correct = expected_incorrect = expected_unanswered = 0
        answer_map = {answer.question_id: answer for answer in attempt.answers.all()}
        for link in ExamQuestion.objects.filter(section__exam=attempt.exam).select_related("question"):
            answer = answer_map.get(link.question_id)
            if answer is None:
                expected_unanswered += 1
                continue
            points, is_correct = score_answer(link.question, answer.value)
            expected_score += points
            if is_correct:
                expected_correct += 1
            else:
                expected_incorrect += 1
        if (
            Decimal(str(payload.get("score", "0"))) != expected_score
            or int(payload.get("correct_count", 0)) != expected_correct
            or int(payload.get("incorrect_count", 0)) != expected_incorrect
            or int(payload.get("unanswered_count", 0)) != expected_unanswered
        ):
            raise ValueError("result_mismatch")
        Attempt.objects.filter(id=attempt.id).update(status=Attempt.Status.SUBMITTED, submitted_at=_parse_datetime(payload.get("submitted_at")) or timezone.now())
        Result.objects.update_or_create(
            attempt=attempt,
            defaults={
                "score": payload.get("score", 0),
                "correct_count": payload.get("correct_count", 0),
                "incorrect_count": payload.get("incorrect_count", 0),
                "unanswered_count": payload.get("unanswered_count", 0),
            },
        )
    event = SyncOutbox.objects.create(
        id=event_id,
        organization=organization,
        event_type=event_type,
        entity_type=envelope.get("aggregate_type", "attempt"),
        entity_id=str(envelope.get("aggregate_id") or attempt_id),
        idempotency_key=envelope.get("idempotency_key") or f"remote:{event_id}",
        payload=payload,
        origin_node=str(envelope.get("origin_node") or "unknown"),
        schema_version=int(envelope.get("schema_version") or 1),
        occurred_at=_parse_datetime(envelope.get("occurred_at")) or timezone.now(),
        delivery_status=SyncOutbox.DeliveryStatus.DELIVERED,
        processed_at=timezone.now(),
        delivered_at=timezone.now(),
    )
    return event, True

def _normalise(value):
    if isinstance(value, list):
        return sorted(str(v) for v in value)
    return str(value).strip()

def validate_answer_value(question, value):
    """Validate an answer against the question's persisted contract."""
    if question.question_type == question.Types.SINGLE:
        if isinstance(value, (list, dict, bool)) or value not in question.options:
            raise ValidationError("Choose one of the available options.")
        return value
    if question.question_type == question.Types.MULTI:
        if not isinstance(value, list) or not value or len(value) != len(set(map(str, value))):
            raise ValidationError("Choose one or more unique available options.")
        if any(option not in question.options for option in value):
            raise ValidationError("Every selected option must be available for this question.")
        return value
    if question.question_type == question.Types.NUMERIC:
        if isinstance(value, bool) or isinstance(value, (list, dict)):
            raise ValidationError("Enter a numeric answer.")
        try:
            number = Decimal(str(value).strip())
        except (ArithmeticError, ValueError):
            raise ValidationError("Enter a numeric answer.")
        if not number.is_finite():
            raise ValidationError("Enter a finite numeric answer.")
        return value
    raise ValidationError("Unsupported question type.")

def score_answer(question, value):
    if question.question_type == question.Types.NUMERIC:
        try:
            is_correct = Decimal(str(question.correct_answer).strip()) == Decimal(str(value).strip())
        except (ArithmeticError, ValueError):
            is_correct = False
    else:
        is_correct = _normalise(question.correct_answer) == _normalise(value)
    if is_correct:
        return question.positive_marks, True
    return -question.negative_marks, False

@transaction.atomic
def expire_attempt_if_needed(*, attempt_id, actor=None):
    """Atomically submit an in-progress attempt whose server deadline passed."""
    attempt = Attempt.objects.select_for_update().select_related("exam", "student").get(id=attempt_id)
    if attempt.status == Attempt.Status.IN_PROGRESS and attempt.is_expired():
        return submit_attempt(attempt_id=attempt.id, actor=actor)
    return attempt, getattr(attempt, "result", None)

@transaction.atomic
def submit_attempt(*, attempt_id, actor=None):
    attempt = Attempt.objects.select_for_update().select_related("exam", "student").get(id=attempt_id)
    if attempt.status == Attempt.Status.SUBMITTED:
        return attempt, attempt.result
    score = Decimal("0")
    correct = incorrect = unanswered = 0
    questions = {eq.question_id: eq.question for section in attempt.exam.sections.all() for eq in section.exam_questions.select_related("question")}
    answers = {answer.question_id: answer for answer in attempt.answers.all()}
    for question_id, question in questions.items():
        answer = answers.get(question_id)
        if not answer:
            unanswered += 1
            continue
        points, is_correct = score_answer(question, answer.value)
        score += points
        if is_correct:
            correct += 1
        else:
            incorrect += 1
    attempt.status = Attempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.save(update_fields=["status", "submitted_at"])
    result, _ = Result.objects.update_or_create(attempt=attempt, defaults={"score": score, "correct_count": correct, "incorrect_count": incorrect, "unanswered_count": unanswered})
    AuditEvent.objects.create(organization=attempt.exam.organization, actor=actor, action="attempt.submitted", entity_type="attempt", entity_id=str(attempt.id), metadata={"score": str(score)})
    answers_payload = [{"question_id": str(answer.question_id), "value": answer.value, "saved_at": answer.saved_at.isoformat()} for answer in attempt.answers.all()]
    create_sync_event(
        organization=attempt.exam.organization,
        event_type="attempt.submitted",
        entity_type="attempt",
        entity_id=attempt.id,
        idempotency_key=f"attempt-submitted:{attempt.id}",
        payload={
            "attempt_id": str(attempt.id),
            "exam_id": str(attempt.exam_id),
            "student_id": str(attempt.student_id),
            "started_at": attempt.started_at.isoformat(),
            "deadline_at": attempt.deadline_at.isoformat(),
            "submitted_at": attempt.submitted_at.isoformat(),
            "answers": answers_payload,
            "score": str(score),
            "correct_count": correct,
            "incorrect_count": incorrect,
            "unanswered_count": unanswered,
        },
    )
    return attempt, result
