from django.conf import settings

from rest_framework import authentication as rf_authentication
from rest_framework import exceptions

from api.users.models import AnonymousAPIUser

class APIKeyAuthentication (rf_authentication.BaseAuthentication):
    API_KEY_HTTP_HEADER = 'X-API-Key'

    def authenticate (this, request):
        api_key = request.headers.get (this.API_KEY_HTTP_HEADER, None)

        if api_key == settings.API_AUTH_ANONYMOUS_KEY:
            return (AnonymousAPIUser (), None)

        if api_key != None:
            raise exceptions.AuthenticationFailed ()

        return None

    def authenticate_header (this, request):
        return this.API_KEY_HTTP_HEADER
