from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin')

class IsSupervisor(BasePermission):
    """
    Allows access to supervisor and admin users.
    """
    def has_permission(self, request, view):
        role = getattr(request.user, 'role', None)
        return bool(request.user and request.user.is_authenticated and role in ['admin', 'supervisor'])

class IsOperator(BasePermission):
    """
    Allows access to operator, supervisor, and admin users.
    """
    def has_permission(self, request, view):
        role = getattr(request.user, 'role', None)
        return bool(request.user and request.user.is_authenticated and role in ['admin', 'supervisor', 'operator'])
