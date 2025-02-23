# permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and is either a driver or staff
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.user_type == 'owner' or request.user.is_staff)
        )