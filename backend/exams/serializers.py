from rest_framework import serializers
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
    class Meta:
        model = Student
        fields = ["id", "name", "student_id", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

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
        return data

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

class ExamSerializer(serializers.ModelSerializer):
    sections = ExamSectionSerializer(many=True, read_only=True)
    class Meta:
        model = Exam
        fields = ["id", "title", "duration_minutes", "available_from", "available_until", "status", "published_at", "created_at", "sections"]
        read_only_fields = ["id", "status", "published_at", "created_at", "sections"]

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

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ["score", "correct_count", "incorrect_count", "unanswered_count", "calculated_at"]

class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    result = serializers.SerializerMethodField()
    class Meta:
        model = Attempt
        fields = ["id", "exam", "student", "status", "started_at", "deadline_at", "submitted_at", "answers", "result"]
        read_only_fields = fields
    def get_result(self, obj):
        return ResultSerializer(obj.result).data if hasattr(obj, "result") else None
