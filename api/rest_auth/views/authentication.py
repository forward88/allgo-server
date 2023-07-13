from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response as APIResponse
from rest_framework import permissions as rf_permissions
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..permissions import ReSTAuthAccess
from ..serializers import RequestPhoneVerificationSerializer, SignInSerializer, RefreshTokensSerializer

class ReSTAuthView (APIView):
    permission_classes = [ReSTAuthAccess]

    def post (this, request):
        serializer = this.serializer_class (data=request.data)
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

@extend_schema_view (
    post=extend_schema (
        description=(
            "SMS verification can be mocked by using phone numbers of the form `+1612555xxxx` and using `811348` " +
            "for the verification code.  This allows test accounts to be made without a valid phone number.")))
class RequestPhoneVerificationView (ReSTAuthView):
    serializer_class = RequestPhoneVerificationSerializer

class SignInView (ReSTAuthView):
    serializer_class = SignInSerializer

class RefreshTokensView (ReSTAuthView):
    serializer_class = RefreshTokensSerializer
