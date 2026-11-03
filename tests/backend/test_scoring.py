from decimal import Decimal
import pytest
from django.utils import timezone
from exams.models import Attempt, Exam, ExamQuestion, ExamSection, Organization, Question, Student, User
from exams.services import score_answer, submit_attempt

@pytest.mark.django_db
def test_single_choice_scoring():
    org = Organization.objects.create(name="Test", slug="test")
    user = User.objects.create_user(username="admin", password="not-used", organization=org, role=User.Roles.ADMIN)
    question = Question.objects.create(organization=org, created_by=user, question_type="single", prompt="2+2?", options=["3", "4"], correct_answer="4", positive_marks=3, negative_marks=1)
    points, correct = score_answer(question, "4")
    assert correct is True and points == Decimal("3")
    points, correct = score_answer(question, "3")
    assert correct is False and points == Decimal("-1")

@pytest.mark.django_db
def test_submission_is_idempotent_and_scores_unanswered():
    org = Organization.objects.create(name="Test", slug="test")
    admin_user = User.objects.create_user(username="admin", password="not-used", organization=org, role=User.Roles.ADMIN)
    student_user = User.objects.create_user(username="student", password="not-used", organization=org, role=User.Roles.STUDENT)
    student = Student.objects.create(organization=org, user=student_user, name="Student", student_id="S1")
    exam = Exam.objects.create(organization=org, created_by=admin_user, title="Test", duration_minutes=10, status=Exam.Status.PUBLISHED)
    section = ExamSection.objects.create(exam=exam, name="Core", position=1)
    q1 = Question.objects.create(organization=org, created_by=admin_user, question_type="single", prompt="Q1", correct_answer="A", positive_marks=1, negative_marks=0)
    q2 = Question.objects.create(organization=org, created_by=admin_user, question_type="single", prompt="Q2", correct_answer="B", positive_marks=1, negative_marks=0)
    ExamQuestion.objects.create(section=section, question=q1, position=1)
    ExamQuestion.objects.create(section=section, question=q2, position=2)
    attempt = Attempt.objects.create(exam=exam, student=student, deadline_at=timezone.now() + timezone.timedelta(minutes=10), idempotency_key="attempt-1")
    from exams.models import Answer
    Answer.objects.create(attempt=attempt, question=q1, value="A")
    _, result = submit_attempt(attempt_id=attempt.id, actor=student_user)
    assert result.score == Decimal("1") and result.unanswered_count == 1
    _, second = submit_attempt(attempt_id=attempt.id, actor=student_user)
    assert second.pk == result.pk
