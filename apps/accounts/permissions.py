from rest_framework import permissions

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to Admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsCashierOrAdminRole(permissions.BasePermission):
    """
    Allows access to Cashier and Admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'CASHIER'])

class IsCustomerRole(permissions.BasePermission):
    """
    Allows access to Student and Faculty users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['STUDENT', 'FACULTY'])
