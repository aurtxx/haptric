import uuid
import json
import os
import hmac
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
from rest_framework.permissions import AllowAny
from .models import Answer, Attempt, AuditEvent, Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Student, Subject, SyncOutbox, User
from .permissions import IsOrgMember, IsOrgStaff, IsStudent, IsStudentOrStaff
from .serializers import AnswerSerializer, AnswerSubmissionSerializer, AttemptSerializer, ExamAssignmentSerializer, ExamQuestionSerializer, ExamSectionSerializer, ExamSerializer, OrganizationSerializer, QuestionSerializer, ResultSerializer, StaffAttemptReviewSerializer, StudentProvisionSerializer, StudentSerializer, SubjectSerializer, UserSerializer
from .services import SYNC_EVENT_TYPES, apply_sync_event, create_sync_event, expire_attempt_if_needed, submit_attempt, validate_answer_value

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
        create_sync_event(
            organization=exam.organization,
            event_type="attempt.started",
            entity_type="attempt",
            entity_id=attempt.id,
            idempotency_key=f"attempt-started:{attempt.id}",
            payload={"attempt_id": str(attempt.id), "exam_id": str(exam.id), "student_id": str(student.id), "started_at": attempt.started_at.isoformat(), "deadline_at": attempt.deadline_at.isoformat()},
        )
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
        create_sync_event(
            organization=attempt.exam.organization,
            event_type="answer.saved",
            entity_type="attempt",
            entity_id=attempt.id,
            idempotency_key=f"answer-saved:{attempt.id}:{question.id}:{answer.saved_at.isoformat()}",
            payload={"attempt_id": str(attempt.id), "exam_id": str(attempt.exam_id), "student_id": str(attempt.student_id), "question_id": str(question.id), "value": answer.value, "saved_at": answer.saved_at.isoformat()},
        )
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
    if request.user.role == User.Roles.STUDENT:
        return JsonResponse({"detail": "Forbidden."}, status=403)
    cursor = request.GET.get("cursor", "")
    events = SyncOutbox.objects.filter(organization_id=request.user.organization_id).order_by("created_at")
    if cursor:
        events = events.filter(created_at__gt=cursor)
    payload = [{
        "event_id": str(event.id),
        "event_type": event.event_type,
        "organization_id": str(event.organization_id),
        "origin_node": event.origin_node,
        "aggregate_type": event.entity_type,
        "aggregate_id": event.entity_id,
        "occurred_at": event.occurred_at.isoformat(),
        "schema_version": event.schema_version,
        "idempotency_key": event.idempotency_key,
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
    } for event in events[:100]]
    return JsonResponse({"events": payload, "next_cursor": payload[-1]["created_at"] if payload else cursor})

@api_view(["POST"])
@decorators.permission_classes([AllowAny])
def sync_push(request):
    expected_token = os.getenv("HAPTRIC_SYNC_TOKEN", "")
    supplied_token = request.headers.get("X-Haptric-Sync-Token", "")
    if not expected_token or not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
        return JsonResponse({"detail": "Node authentication required."}, status=401)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)
    events = payload.get("events")
    if not isinstance(events, list) or len(events) > 100 or len(request.body or b"") > 1_000_000:
        return JsonResponse({"detail": "events must be a list of at most 100 items."}, status=400)
    organization_id = payload.get("organization_id")
    expected_organization_id = os.getenv("HAPTRIC_SYNC_ORGANIZATION_ID", "")
    if not expected_organization_id or str(organization_id) != expected_organization_id:
        return JsonResponse({"detail": "Organization is not authorized for this node."}, status=403)
    from .models import Organization
    organization = Organization.objects.filter(id=organization_id).first()
    if not organization:
        return JsonResponse({"detail": "Unknown organization."}, status=403)
    accepted, conflicts = [], []
    for envelope in events:
        if not isinstance(envelope, dict) or len(json.dumps(envelope)) > 200_000:
            return JsonResponse({"detail": "Malformed event."}, status=400)
        if envelope.get("schema_version") != 1 or envelope.get("event_type") not in SYNC_EVENT_TYPES:
            return JsonResponse({"detail": "Unsupported event contract."}, status=400)
        if not envelope.get("event_id") or not envelope.get("idempotency_key") or not envelope.get("origin_node"):
            return JsonResponse({"detail": "Event envelope is incomplete."}, status=400)
        if envelope.get("origin_node") == os.getenv("HAPTRIC_NODE_ID", "local-node"):
            return JsonResponse({"detail": "Origin node must differ from the receiving node."}, status=400)
        if envelope.get("organization_id") and str(envelope.get("organization_id")) != str(organization.id):
            return JsonResponse({"detail": "Organization mismatch."}, status=403)
        try:
            event, created = apply_sync_event(envelope=envelope, organization=organization)
        except PermissionError:
            return JsonResponse({"detail": "Organization mismatch."}, status=403)
        except RuntimeError as exc:
            if str(exc) == "event_conflict":
                conflicts.append(envelope.get("event_id"))
                continue
            return JsonResponse({"detail": "Event conflict."}, status=409)
        except (ValueError, KeyError, Exam.DoesNotExist, Student.DoesNotExist, Attempt.DoesNotExist, ExamQuestion.DoesNotExist) as exc:
            return JsonResponse({"detail": "Event rejected.", "reason": str(exc)}, status=400)
        accepted.append(str(event.id))
    return JsonResponse({"accepted_event_ids": accepted, "conflicts": conflicts})


@api_view(["GET"])
def sync_status(request):
    if not request.user.is_authenticated or not request.user.organization_id:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    if request.user.role == User.Roles.STUDENT:
        return JsonResponse({"detail": "Forbidden."}, status=403)
    qs = SyncOutbox.objects.filter(organization_id=request.user.organization_id)
    latest = qs.filter(delivery_status=SyncOutbox.DeliveryStatus.DELIVERED).order_by("-delivered_at").first()
    pending = qs.filter(delivery_status=SyncOutbox.DeliveryStatus.PENDING).count()
    failed = qs.filter(delivery_status=SyncOutbox.DeliveryStatus.FAILED).count()
    conflict = qs.filter(delivery_status=SyncOutbox.DeliveryStatus.CONFLICT).count()
    delivered = qs.filter(delivery_status=SyncOutbox.DeliveryStatus.DELIVERED).count()
    last_error = qs.exclude(last_error="").order_by("-created_at").values_list("last_error", flat=True).first()
    return JsonResponse({
        "node_id": os.getenv("HAPTRIC_NODE_ID", "local-node"),
        "node_role": os.getenv("HAPTRIC_NODE_ROLE", "lan"),
        "upstream_configured": bool(os.getenv("HAPTRIC_SYNC_URL")),
        "upstream_url": os.getenv("HAPTRIC_SYNC_URL") or None,
        "pending_events": pending,
        "failed_events": failed,
        "conflict_events": conflict,
        "delivered_events": delivered,
        "last_successful_sync": latest.delivered_at.isoformat() if latest and latest.delivered_at else None,
        "last_error": last_error,
    })
