from rest_framework.permissions import BasePermission

class IsOrgMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.organization_id)

class IsOrgStaff(IsOrgMember):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in {"owner", "admin", "teacher", "invigilator"}

class IsStudent(IsOrgMember):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "student"

class IsStudentOrStaff(IsOrgMember):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in {"student", "owner", "admin", "teacher", "invigilator"}
