from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import AuditEvent, Attempt, Result, SyncOutbox

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
    SyncOutbox.objects.get_or_create(idempotency_key=f"attempt-submitted:{attempt.id}", defaults={"organization": attempt.exam.organization, "event_type": "attempt.submitted", "entity_type": "attempt", "entity_id": str(attempt.id), "payload": {"attempt_id": str(attempt.id), "score": str(score)}})
    return attempt, result
