from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Answer, Attempt, AuditEvent, Exam, ExamAssignment, ExamQuestion, ExamSection, Organization, Question, Result, Student, Subject, SyncOutbox, User
for model in [Organization, Student, Subject, Question, Exam, ExamSection, ExamQuestion, ExamAssignment, Attempt, Answer, Result, AuditEvent, SyncOutbox]:
    admin.site.register(model)
admin.site.register(User, UserAdmin)
