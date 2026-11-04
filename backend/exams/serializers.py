from rest_framework import serializers
from .services import score_answer
from .models import Answer, Attempt, Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Result, Student, Subject, User

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "mode", "installation_id", "created_at"]
        read_only_fields = ["id", "installation_id", "created_at"]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "organization"]
        read_only_fields = ["id", "organization"]

class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, allow_null=True)
    class Meta:
        model = Student
        fields = ["id", "name", "student_id", "username", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

class StudentProvisionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
    student_id = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    username = serializers.CharField(max_length=150, allow_blank=True, required=False, trim_whitespace=True)
    temporary_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        request = self.context.get("request")
        organization_id = getattr(getattr(request, "user", None), "organization_id", None)
        username = attrs.get("username") or attrs["student_id"]
        attrs["username"] = username
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "A user with this login ID already exists."})
        if organization_id and Student.objects.filter(organization_id=organization_id, student_id=attrs["student_id"]).exists():
            raise serializers.ValidationError({"student_id": "A student with this ID already exists in this organization."})
        return attrs

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]
        read_only_fields = ["id"]

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "subject", "question_type", "prompt", "options", "correct_answer", "positive_marks", "negative_marks", "version"]
        read_only_fields = ["id", "version"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and getattr(getattr(request, "user", None), "role", None) == User.Roles.STUDENT:
            data.pop("correct_answer", None)
            data.pop("positive_marks", None)
            data.pop("negative_marks", None)
        return data

    def validate(self, attrs):
        prompt = attrs.get("prompt", getattr(self.instance, "prompt", ""))
        if not str(prompt).strip():
            raise serializers.ValidationError({"prompt": "Prompt is required."})
        question_type = attrs.get("question_type", getattr(self.instance, "question_type", None))
        options = attrs.get("options", getattr(self.instance, "options", [])) or []
        correct_answer = attrs.get("correct_answer", getattr(self.instance, "correct_answer", None))
        positive_marks = attrs.get("positive_marks", getattr(self.instance, "positive_marks", 1))
        negative_marks = attrs.get("negative_marks", getattr(self.instance, "negative_marks", 0))
        if question_type in {Question.Types.SINGLE, Question.Types.MULTI} and not options:
            raise serializers.ValidationError({"options": "Choice questions require at least one option."})
        if question_type == Question.Types.SINGLE and isinstance(correct_answer, list):
            raise serializers.ValidationError({"correct_answer": "Single-choice questions require one correct answer."})
        if question_type == Question.Types.MULTI and not isinstance(correct_answer, list):
            raise serializers.ValidationError({"correct_answer": "Multiple-choice questions require a list of correct answers."})
        if question_type in {Question.Types.SINGLE, Question.Types.MULTI}:
            answer_values = correct_answer if isinstance(correct_answer, list) else [correct_answer]
            invalid = [value for value in answer_values if value not in options]
            if invalid:
                raise serializers.ValidationError({"correct_answer": "Every correct answer must be one of the options."})
        if positive_marks < 0 or negative_marks < 0:
            raise serializers.ValidationError({"positive_marks": "Marks cannot be negative."})
        return attrs

class ExamQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    question_id = serializers.PrimaryKeyRelatedField(source="question", queryset=Question.objects.all(), write_only=True)
    class Meta:
        model = ExamQuestion
        fields = ["id", "question", "question_id", "position"]
        read_only_fields = ["id"]

class ExamSectionSerializer(serializers.ModelSerializer):
    exam_questions = ExamQuestionSerializer(many=True, read_only=True)
    class Meta:
        model = ExamSection
        fields = ["id", "name", "position", "exam_questions"]
        read_only_fields = ["id", "exam_questions"]

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", ""))
        position = attrs.get("position", getattr(self.instance, "position", 1))
        if not str(name).strip():
            raise serializers.ValidationError({"name": "Section name is required."})
        if position < 1:
            raise serializers.ValidationError({"position": "Section position must be at least 1."})
        return attrs

class ExamSerializer(serializers.ModelSerializer):
    sections = ExamSectionSerializer(many=True, read_only=True)
    class Meta:
        model = Exam
        fields = ["id", "title", "duration_minutes", "available_from", "available_until", "status", "published_at", "created_at", "sections"]
        read_only_fields = ["id", "status", "published_at", "created_at", "sections"]

    def validate(self, attrs):
        title = attrs.get("title", getattr(self.instance, "title", ""))
        duration = attrs.get("duration_minutes", getattr(self.instance, "duration_minutes", None))
        available_from = attrs.get("available_from", getattr(self.instance, "available_from", None))
        available_until = attrs.get("available_until", getattr(self.instance, "available_until", None))
        if not str(title).strip():
            raise serializers.ValidationError({"title": "Title is required."})
        if duration is None or not 1 <= duration <= 240:
            raise serializers.ValidationError({"duration_minutes": "Duration must be between 1 and 240 minutes."})
        if available_from and available_until and available_from >= available_until:
            raise serializers.ValidationError({"available_until": "The closing time must be after the opening time."})
        return attrs

class ExamAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAssignment
        fields = ["id", "exam", "student", "assigned_at"]
        read_only_fields = ["id", "assigned_at"]

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "question", "value", "saved_at"]
        read_only_fields = ["id", "saved_at"]

class AnswerSubmissionSerializer(serializers.Serializer):
    question = serializers.UUIDField()
    value = serializers.JSONField()

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ["score", "correct_count", "incorrect_count", "unanswered_count", "calculated_at"]

class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    result = serializers.SerializerMethodField()
    # These display fields make the organization-scoped staff review payload
    # useful without requiring the client to issue one request per relation.
    # They are intentionally read-only and contain no scoring or answer-key
    # data. Students can only receive their own attempt rows (see the viewset
    # queryset), so exposing the labels does not widen student access.
    student_name = serializers.CharField(source="student.name", read_only=True)
    student_id = serializers.CharField(source="student.student_id", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    class Meta:
        model = Attempt
        fields = [
            "id",
            "exam",
            "exam_title",
            "student",
            "student_name",
            "student_id",
            "status",
            "started_at",
            "deadline_at",
            "submitted_at",
            "answers",
            "result",
        ]
        read_only_fields = fields
    def get_result(self, obj):
        return ResultSerializer(obj.result).data if hasattr(obj, "result") else None


class StaffAttemptReviewSerializer(serializers.Serializer):
    """Explicit staff-only attempt review contract.

    The regular AttemptSerializer is intentionally shared with students and
    never contains answer keys. This representation is only used by the
    staff-protected ``review`` action and reveals correctness after submission.
    """

    id = serializers.UUIDField(read_only=True)
    student = serializers.UUIDField(source="student.id", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)
    student_id = serializers.CharField(source="student.student_id", read_only=True)
    exam = serializers.UUIDField(source="exam.id", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    status = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    deadline_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    result = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    def get_result(self, obj):
        result = getattr(obj, "result", None)
        return ResultSerializer(result).data if result else None

    def get_questions(self, obj):
        submitted = obj.status == Attempt.Status.SUBMITTED
        answers = {answer.question_id: answer for answer in obj.answers.all()}
        rows = []
        sections = obj.exam.sections.all()
        for section in sections:
            for link in section.exam_questions.all():
                question = link.question
                answer = answers.get(question.id)
                response_value = answer.value if answer else None
                state = "unanswered"
                marks_awarded = "0.00"
                if answer and submitted:
                    awarded, is_correct = score_answer(question, answer.value)
                    state = "correct" if is_correct else "incorrect"
                    marks_awarded = str(awarded)
                elif answer and not submitted:
                    state = "pending"
                    marks_awarded = None
                row = {
                    "question_id": str(question.id),
                    "section_id": str(section.id),
                    "section_name": section.name,
                    "section_position": section.position,
                    "position": link.position,
                    "prompt": question.prompt,
                    "question_type": question.question_type,
                    "options": question.options,
                    "student_response": response_value,
                    "answer_state": state,
                    "marks_awarded": marks_awarded,
                }
                # Correctness and answer keys are deliberately withheld while
                # an attempt is active; staff review becomes complete only
                # after the persisted submission transition.
                if submitted:
                    row["correct_answer"] = question.correct_answer
                rows.append(row)
        return rows
