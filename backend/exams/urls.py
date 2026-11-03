from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AttemptViewSet, ExamQuestionViewSet, ExamSectionViewSet, ExamViewSet, OrganizationViewSet, QuestionViewSet, StudentViewSet, SubjectViewSet, UserViewSet, auth_login, auth_logout, csrf, health, me, sync_pull, sync_push

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("users", UserViewSet, basename="user")
router.register("students", StudentViewSet, basename="student")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("questions", QuestionViewSet, basename="question")
router.register("exams", ExamViewSet, basename="exam")
router.register("sections", ExamSectionViewSet, basename="section")
router.register("exam-questions", ExamQuestionViewSet, basename="exam-question")
router.register("attempts", AttemptViewSet, basename="attempt")
urlpatterns = [path("health/", health), path("auth/csrf/", csrf), path("auth/login/", auth_login), path("auth/logout/", auth_logout), path("me/", me), path("sync/pull/", sync_pull), path("sync/push/", sync_push)] + router.urls
