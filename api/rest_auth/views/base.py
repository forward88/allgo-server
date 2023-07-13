from rest_framework.views import APIView
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from api.rest_auth.authentication import APIKeyAuthentication, JWTAuthentication
from api.rest_auth.permissions import AnonymousAPIUserAccess, ActiveAPIUserAccess

from api.users.models import APIUser

__all__ = ['AnonymousAPIUserView', 'ActiveAPIUserView', 'LateralUserView']

class AnonymousAPIUserView (APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [AnonymousAPIUserAccess]

class ActiveAPIUserView (APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [ActiveAPIUserAccess]

class LateralUserView (ActiveAPIUserView):
    def initial (this, request, *args, **kwargs):
        super ().initial (request, *args, **kwargs)

        this.session_user = request.user
        this.query_user = this.session_user

        query_user_id = request.GET.get ('user_id', None)

        if query_user_id is not None:
            this.query_user = APIUser.objects.filter (pk=query_user_id).first ()

# OpenAPI security scheme registration

class APIKeyAuthenticationScheme (OpenApiAuthenticationExtension):
    target_class = APIKeyAuthentication
    name = 'APIKeyAuth'

    def get_security_definition (this, auto_schema):
        return { 'type': 'apiKey', 'in': 'header', 'name': 'X-API-Key' }

class JWTAuthenticationScheme (OpenApiAuthenticationExtension):
    target_class = JWTAuthentication
    name = 'JWTAuth'

    def get_security_definition (this, auto_schema):
        return { 'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT' }
