from rest_framework import permissions as rf_permissions

from api.users.models import APIUser, AnonymousAPIUser

class ReSTAuthAccess (rf_permissions.BasePermission):
    def has_permission (this, request, view):
        return type (request.user) == AnonymousAPIUser

class AnonymousAPIUserAccess (rf_permissions.BasePermission):
    def has_permission (this, request, view):
        return (type (request.user) == AnonymousAPIUser) and (request.method in rf_permissions.SAFE_METHODS)

class ActiveAPIUserAccess (rf_permissions.BasePermission):
    def has_permission (this, request, view):
        return (type (request.user) == APIUser) and request.user.active
