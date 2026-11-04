import uuid
import json
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework import decorators, response, serializers, status, viewsets
from rest_framework.decorators import api_view
from .models import Answer, Attempt, AuditEvent, Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Student, Subject, SyncOutbox, User
from .permissions import IsOrgMember, IsOrgStaff, IsStudent, IsStudentOrStaff
from .serializers import AnswerSerializer, AnswerSubmissionSerializer, AttemptSerializer, ExamAssignmentSerializer, ExamQuestionSerializer, ExamSectionSerializer, ExamSerializer, OrganizationSerializer, QuestionSerializer, ResultSerializer, StaffAttemptReviewSerializer, StudentProvisionSerializer, StudentSerializer, SubjectSerializer, UserSerializer
from .services import expire_attempt_if_needed, submit_attempt, validate_answer_value

def health(_request):
    return JsonResponse({"status": "ok", "service": "exam-platform-api"})

def csrf(_request):
    return JsonResponse({"csrfToken": get_token(_request)})

@csrf_protect
def auth_login(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed.", "code": "method_not_allowed"}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON.", "code": "invalid_json"}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "A JSON object is required.", "code": "validation_error"}, status=400)
    username = payload.get("username", "")
    password = payload.get("password", "")
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password:
        return JsonResponse({"detail": "Username and password are required.", "code": "validation_error"}, status=400)
    user = authenticate(request, username=username, password=password)
    if not user or not user.is_active or not user.organization_id:
        return JsonResponse({"detail": "Invalid credentials.", "code": "authentication_failed"}, status=401)
    login(request, user)
    return JsonResponse({"id": str(user.id), "username": user.username, "role": user.role, "organization": str(user.organization_id)})

@csrf_protect
def auth_logout(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed.", "code": "method_not_allowed"}, status=405)
    logout(request)
    return JsonResponse({"status": "ok"})

def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required.", "code": "authentication_required"}, status=401)
    return JsonResponse({"id": str(request.user.id), "username": request.user.username, "role": request.user.role, "organization": str(request.user.organization_id)})

class ScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOrgMember]
    organization_field = "organization"
    def get_queryset(self):
        return super().get_queryset().filter(**{f"{self.organization_field}_id": self.request.user.organization_id})
    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrgMember]
    def get_queryset(self):
        return Organization.objects.filter(id=self.request.user.organization_id)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsOrgStaff]
    def get_queryset(self):
        return User.objects.filter(organization_id=self.request.user.organization_id)

class StudentViewSet(ScopedViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsOrgStaff]

    def create(self, request, *args, **kwargs):
        return response.Response({"detail": "Use the provision action to create a student login."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @decorators.action(detail=False, methods=["post"])
    @transaction.atomic
    def provision(self, request):
        serializer = StudentProvisionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User(username=data["username"], organization=request.user.organization, role=User.Roles.STUDENT, is_active=data["is_active"])
            user.set_password(data["temporary_password"])
            user.save()
            student = Student.objects.create(organization=request.user.organization, user=user, name=data["name"], student_id=data["student_id"], is_active=data["is_active"])
        except IntegrityError:
            raise serializers.ValidationError({"detail": "The login ID or student ID is already in use."})
        AuditEvent.objects.create(organization=request.user.organization, actor=request.user, action="student.provisioned", entity_type="student", entity_id=str(student.id), metadata={"username": user.username})
        return response.Response(StudentSerializer(student, context={"request": request}).data, status=status.HTTP_201_CREATED)

class SubjectViewSet(ScopedViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsOrgStaff]

class QuestionViewSet(ScopedViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsOrgStaff]
    def perform_create(self, serializer):
        subject = serializer.validated_data.get("subject")
        if subject and subject.organization_id != self.request.user.organization_id:
            raise serializers.ValidationError({"subject": "Subject belongs to another organization."})
        serializer.save(organization=self.request.user.organization, created_by=self.request.user)

    def _published_exam_question(self, question):
        return question.exam_questions.filter(section__exam__status=Exam.Status.PUBLISHED).exists()

    def perform_update(self, serializer):
        if self._published_exam_question(serializer.instance):
            raise serializers.ValidationError({"question": "Question content is immutable after publication."})
        subject = serializer.validated_data.get("subject")
        if subject and subject.organization_id != self.request.user.organization_id:
            raise serializers.ValidationError({"subject": "Subject belongs to another organization."})
        serializer.save()

    def perform_destroy(self, instance):
        if self._published_exam_question(instance):
            raise serializers.ValidationError({"question": "Question content is immutable after publication."})
        instance.delete()

class ExamViewSet(ScopedViewSet):
    queryset = Exam.objects.all().prefetch_related("sections__exam_questions__question")
    serializer_class = ExamSerializer
    permission_classes = [IsOrgMember]
    def get_permissions(self):
        if self.action in {"list", "retrieve"} and self.request.user.role == User.Roles.STUDENT:
            return [IsOrgMember()]
        return [IsOrgStaff()]
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == User.Roles.STUDENT:
            return queryset.filter(assignments__student__user=self.request.user, status=Exam.Status.PUBLISHED).distinct()
        return queryset
    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization, created_by=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.status == Exam.Status.PUBLISHED:
            raise serializers.ValidationError({"exam": "Published exams are immutable."})
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status == Exam.Status.PUBLISHED:
            raise serializers.ValidationError({"exam": "Published exams cannot be deleted."})
        instance.delete()
    @decorators.action(detail=True, methods=["post"])
    @transaction.atomic
    def publish(self, request, pk=None):
        exam = self.get_object()
        if not exam.sections.filter(exam_questions__isnull=False).exists():
            return response.Response({"detail": "An exam needs at least one question before publishing."}, status=status.HTTP_409_CONFLICT)
        exam.status = Exam.Status.PUBLISHED
        exam.published_at = timezone.now()
        exam.save(update_fields=["status", "published_at"])
        AuditEvent.objects.create(organization=exam.organization, actor=request.user, action="exam.published", entity_type="exam", entity_id=str(exam.id))
        return response.Response(self.get_serializer(exam).data)
    @decorators.action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        exam = self.get_object()
        if exam.status != Exam.Status.PUBLISHED:
            return response.Response({"detail": "Only published exams can be assigned."}, status=status.HTTP_409_CONFLICT)
        student = get_object_or_404(Student, id=request.data.get("student"), organization_id=request.user.organization_id)
        assignment, created = ExamAssignment.objects.get_or_create(exam=exam, student=student)
        if created:
            AuditEvent.objects.create(organization=exam.organization, actor=request.user, action="exam.assigned", entity_type="assignment", entity_id=str(assignment.id), metadata={"student_id": str(student.id)})
        return response.Response(ExamAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ExamSectionViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSectionSerializer
    permission_classes = [IsOrgStaff]
    def get_queryset(self):
        return ExamSection.objects.filter(exam__organization_id=self.request.user.organization_id)
    def perform_create(self, serializer):
        exam = get_object_or_404(Exam, id=self.request.data.get("exam"), organization_id=self.request.user.organization_id)
        if exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        serializer.save(exam=exam)

    def perform_update(self, serializer):
        if serializer.instance.exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        serializer.save()

    def perform_destroy(self, instance):
        if instance.exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        instance.delete()

class ExamQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = ExamQuestionSerializer
    permission_classes = [IsOrgStaff]
    def get_queryset(self):
        return ExamQuestion.objects.filter(section__exam__organization_id=self.request.user.organization_id)
    def perform_create(self, serializer):
        section = get_object_or_404(ExamSection, id=self.request.data.get("section"), exam__organization_id=self.request.user.organization_id)
        if section.exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        question = get_object_or_404(Question, id=self.request.data.get("question_id"), organization_id=self.request.user.organization_id)
        serializer.save(section=section, question=question)

    def perform_update(self, serializer):
        if serializer.instance.section.exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        question = serializer.validated_data.get("question")
        if question and question.organization_id != self.request.user.organization_id:
            raise serializers.ValidationError({"question_id": "Question belongs to another organization."})
        serializer.save()

    def perform_destroy(self, instance):
        if instance.section.exam.status != Exam.Status.DRAFT:
            raise serializers.ValidationError({"exam": "Published exam content is immutable."})
        instance.delete()

class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttemptSerializer
    permission_classes = [IsOrgMember]
    def get_queryset(self):
        # Staff review is organization-scoped. Keep all related display data
        # in this query so the review list does not perform per-row lookups.
        qs = Attempt.objects.filter(
            exam__organization_id=self.request.user.organization_id,
        ).select_related(
            "exam",
            "student",
            "student__user",
            "result",
        ).prefetch_related("answers", "exam__sections__exam_questions__question")
        if self.request.user.role == User.Roles.STUDENT:
            qs = qs.filter(student__user=self.request.user)
        return qs

    def _expire_visible_attempts(self, attempts):
        for attempt in attempts:
            if attempt.status == Attempt.Status.IN_PROGRESS and attempt.is_expired():
                expire_attempt_if_needed(attempt_id=attempt.id, actor=self.request.user)
                attempt.refresh_from_db()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        attempts = list(queryset)
        self._expire_visible_attempts(attempts)
        serializer = self.get_serializer(attempts, many=True)
        return response.Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == Attempt.Status.IN_PROGRESS and instance.is_expired():
            expire_attempt_if_needed(attempt_id=instance.id, actor=request.user)
            instance = self.get_queryset().get(id=instance.id)
        return response.Response(self.get_serializer(instance).data)

    @decorators.action(detail=True, methods=["get"], permission_classes=[IsOrgStaff], url_path="review")
    def review(self, request, pk=None):
        """Return server-derived question review data to authorized staff only."""
        attempt = self.get_object()
        return response.Response(StaffAttemptReviewSerializer(attempt).data)

    @decorators.action(detail=False, methods=["post"], permission_classes=[IsStudent])
    @transaction.atomic
    def start(self, request):
        exam = get_object_or_404(Exam, id=request.data.get("exam"), organization_id=request.user.organization_id, status=Exam.Status.PUBLISHED)
        now = timezone.now()
        if exam.available_from and now < exam.available_from:
            return response.Response({"detail": "This exam is not open yet."}, status=status.HTTP_409_CONFLICT)
        if exam.available_until and now >= exam.available_until:
            return response.Response({"detail": "This exam is closed."}, status=status.HTTP_409_CONFLICT)
        student = get_object_or_404(Student, user=request.user, organization_id=request.user.organization_id, is_active=True)
        if not ExamAssignment.objects.filter(exam=exam, student=student).exists():
            return response.Response({"detail": "Exam is not assigned to this student."}, status=status.HTTP_403_FORBIDDEN)
        # Lock the student row so rapid clicks/two tabs cannot create two active attempts.
        student = Student.objects.select_for_update().get(id=student.id)
        existing = Attempt.objects.select_for_update().filter(exam=exam, student=student).order_by("started_at").first()
        if existing:
            if existing.status == Attempt.Status.IN_PROGRESS and existing.is_expired():
                submit_attempt(attempt_id=existing.id, actor=request.user)
                existing = Attempt.objects.select_related("result").get(id=existing.id)
            return response.Response(self.get_serializer(existing).data)
        started = timezone.now()
        idempotency_key = request.headers.get("Idempotency-Key") or str(uuid.uuid4())
        attempt = Attempt.objects.create(exam=exam, student=student, started_at=started, deadline_at=started + timedelta(minutes=exam.duration_minutes), idempotency_key=idempotency_key)
        return response.Response(self.get_serializer(attempt).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["put", "patch"], permission_classes=[IsStudent])
    @transaction.atomic
    def answer(self, request, pk=None):
        attempt = self.get_object()
        attempt = Attempt.objects.select_for_update().select_related("student").get(id=attempt.id)
        if attempt.student.user_id != request.user.id:
            return response.Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        if attempt.status != Attempt.Status.IN_PROGRESS or attempt.is_expired():
            if attempt.status == Attempt.Status.IN_PROGRESS and attempt.is_expired():
                submit_attempt(attempt_id=attempt.id, actor=request.user)
            return response.Response({"detail": "Attempt is closed."}, status=status.HTTP_409_CONFLICT)
        payload = AnswerSubmissionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        question = get_object_or_404(Question, id=payload.validated_data["question"], organization_id=request.user.organization_id, exam_questions__section__exam=attempt.exam)
        try:
            validate_answer_value(question, payload.validated_data["value"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"value": str(exc)})
        answer, _ = Answer.objects.update_or_create(attempt=attempt, question=question, defaults={"value": payload.validated_data["value"]})
        return response.Response(AnswerSerializer(answer).data)

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsStudentOrStaff])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if request.user.role == User.Roles.STUDENT and attempt.student.user_id != request.user.id:
            return response.Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        _, result = submit_attempt(attempt_id=attempt.id, actor=request.user)
        return response.Response(ResultSerializer(result).data)

@api_view(["GET"])
def sync_pull(request):
    if not request.user.is_authenticated or not request.user.organization_id:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    cursor = request.GET.get("cursor", "")
    events = SyncOutbox.objects.filter(organization_id=request.user.organization_id).order_by("created_at")
    if cursor:
        events = events.filter(created_at__gt=cursor)
    payload = [{"event_id": str(event.id), "event_type": event.event_type, "entity_type": event.entity_type, "entity_id": event.entity_id, "payload": event.payload, "created_at": event.created_at.isoformat()} for event in events[:100]]
    return JsonResponse({"events": payload, "next_cursor": payload[-1]["created_at"] if payload else cursor})

@api_view(["POST"])
def sync_push(request):
    if not request.user.is_authenticated or not request.user.organization_id:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)
    accepted = []
    for envelope in payload.get("events", []):
        key = envelope.get("idempotency_key")
        if not key:
            return JsonResponse({"detail": "Every event requires an idempotency_key."}, status=400)
        existing = SyncOutbox.objects.filter(idempotency_key=key).first()
        if existing and existing.organization_id != request.user.organization_id:
            return JsonResponse({"detail": "Idempotency key belongs to another organization."}, status=409)
        event = existing or SyncOutbox.objects.create(idempotency_key=key, organization=request.user.organization, event_type=envelope.get("event_type", "sync.event"), entity_type=envelope.get("entity_type", "unknown"), entity_id=envelope.get("entity_id", ""), payload=envelope.get("payload", {}))
        accepted.append(str(event.id))
    return JsonResponse({"accepted_event_ids": accepted})
