from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import AuditEvent, Attempt, Result, SyncOutbox

def _normalise(value):
    if isinstance(value, list):
        return sorted(str(v) for v in value)
    return str(value).strip()

def score_answer(question, value):
    if _normalise(question.correct_answer) == _normalise(value):
        return question.positive_marks, True
    return -question.negative_marks, False

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
    SyncOutbox.objects.get_or_create(idempotency_key=f"attempt-submitted:{attempt.id}", defaults={"organization": attempt.exam.organization, "event_type": "attempt.submitted", "entity_type": "attempt", "entity_id": str(attempt.id), "payload": {"attempt_id": str(attempt.id), "score": str(score)}})
    return attempt, result
