import enum

import jwt
from rest_framework import authentication
from rest_framework import exceptions

from api.users.models import APIUser
from ..utils import extract_access_token_data

__all__ = ['JWTAuthErrorMessage', 'JWTAuthentication']

class JWTAuthErrorMessage (enum.Enum):
    EXPIRED_TOKEN = "Access token has expired."
    INVALID_TOKEN = "Access token is invalid."

class JWTAuthentication (authentication.BaseAuthentication):
    ACCESS_TOKEN_HTTP_HEADER = 'Authorization'
    ACCESS_TOKEN_HEADER_TYPE = 'Bearer'

    def authenticate (this, request):
        auth_header_value = request.headers.get (this.ACCESS_TOKEN_HTTP_HEADER, None)

        if auth_header_value is None or not auth_header_value.startswith (this.ACCESS_TOKEN_HEADER_TYPE):
            return None

        access_token = auth_header_value.replace (this.ACCESS_TOKEN_HEADER_TYPE, '', 1).strip ()

        try:
            api_user_id = extract_access_token_data (access_token)
        except jwt.exceptions.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed (detail=JWTAuthErrorMessage.EXPIRED_TOKEN.value)
        except jwt.exceptions.DecodeError:
            raise exceptions.AuthenticationFailed (detail=JWTAuthErrorMessage.INVALID_TOKEN.value)

        api_user = APIUser.objects.get (pk=api_user_id)

        if not api_user.is_authenticated:
            return None

        api_user.register_access ()

        return (api_user, None)

    def authenticate_header (this, request):
        return this.ACCESS_TOKEN_HEADER_TYPE
