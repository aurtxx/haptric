import uuid
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    mode = models.CharField(max_length=10, choices=[("lan", "LAN"), ("cloud", "Cloud")], default="lan")
    installation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class User(AbstractUser):
    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Exam administrator"
        TEACHER = "teacher", "Teacher"
        INVIGILATOR = "invigilator", "Invigilator"
        STUDENT = "student", "Student"
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE, related_name="users")
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)

class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="students")
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="student_profile")
    name = models.CharField(max_length=200)
    student_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "student_id"], name="uniq_student_id_per_org")]

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=120)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="uniq_subject_per_org")]

class Question(models.Model):
    class Types(models.TextChoices):
        SINGLE = "single", "Single choice"
        MULTI = "multi", "Multiple choice"
        NUMERIC = "numeric", "Numerical value"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="questions")
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL, related_name="questions")
    question_type = models.CharField(max_length=12, choices=Types.choices)
    prompt = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.JSONField()
    positive_marks = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1"))
    negative_marks = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_questions")
    created_at = models.DateTimeField(auto_now_add=True)

class Exam(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=200)
    duration_minutes = models.PositiveIntegerField(default=10)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_exams")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        if not 1 <= self.duration_minutes <= 240:
            raise ValidationError({"duration_minutes": "Duration must be between 1 and 240 minutes."})
        if self.available_from and self.available_until and self.available_from >= self.available_until:
            raise ValidationError({"available_until": "The closing time must be after the opening time."})

class ExamSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=120)
    position = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["exam", "position"], name="uniq_section_position")]

class ExamQuestion(models.Model):
    section = models.ForeignKey(ExamSection, on_delete=models.CASCADE, related_name="exam_questions")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="exam_questions")
    position = models.PositiveIntegerField()
    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["section", "position"], name="uniq_question_position")]

class ExamAssignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["exam", "student"], name="uniq_exam_student_assignment")]

class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        SUBMITTED = "submitted", "Submitted"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="attempts")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="attempts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(default=timezone.now)
    deadline_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    def is_expired(self, at=None):
        return (at or timezone.now()) >= self.deadline_at

class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    value = models.JSONField()
    saved_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["attempt", "question"], name="uniq_attempt_question_answer")]

class Result(models.Model):
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name="result")
    score = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    calculated_at = models.DateTimeField(auto_now_add=True)

class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SyncOutbox(models.Model):
    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        CONFLICT = "conflict", "Conflict"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sync_outbox")
    event_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=100)
    idempotency_key = models.CharField(max_length=128, unique=True)
    payload = models.JSONField(default=dict)
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    origin_node = models.CharField(max_length=120, default="local")
    schema_version = models.PositiveIntegerField(default=1)
    occurred_at = models.DateTimeField(default=timezone.now)
    delivery_status = models.CharField(max_length=16, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    last_error = models.CharField(max_length=500, blank=True, default="")
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
