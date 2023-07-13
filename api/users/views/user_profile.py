from rest_framework.response import Response as APIResponse
from rest_framework.request import Request
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes

from api.users.serializers import (
    CheckNicknameAvailabilitySerializer,
    ClaimNicknameSerializer,
    UserProfileDetailSerializer,
    UserProfileOptionsSerializer,
    UserProfileEditSerializer,
    UserAccountDeleteSerializer
)
from api.rest_auth.views import ActiveAPIUserView, AnonymousAPIUserView, LateralUserView
from api.users.models import UserProfile

__all__ = ['CheckNicknameAvailabilityView', 'ClaimNicknameView',
           'UserProfileDetailView', 'UserProfileOptionsView',
           'UserProfileEditView', 'UserDeleteAccountView']


class NicknameView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='nickname',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True) ] )
    def get (this, request):
        query_params = request.GET.dict ()

        serializer = this.serializer_class (data=query_params, context={'user': request.user})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class CheckNicknameAvailabilityView (NicknameView):
    serializer_class = CheckNicknameAvailabilitySerializer

class ClaimNicknameView (NicknameView):
    serializer_class = ClaimNicknameSerializer


class UserProfileDetailView (LateralUserView):
    @extend_schema (
        description="Returns general information for the user specified by the provided access token or user_id parameter.",
        parameters=[
            OpenApiParameter (
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False) ],
        responses=UserProfileDetailSerializer)
    def get (self, request: Request):
        user_profile = self.query_user.user_profile

        serializer = UserProfileDetailSerializer(user_profile)

        return APIResponse (serializer.data)


class UserProfileOptionsView (AnonymousAPIUserView):
    @extend_schema (responses=UserProfileOptionsSerializer)
    def get (this, request):
        serializer = UserProfileOptionsSerializer (data={})
        serializer.is_valid ()

        return APIResponse (serializer.validated_data)

class UserProfileEditView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='nickname',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False),
            OpenApiParameter (
                name='avatar_name',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False),
            OpenApiParameter (
                name='background_color_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False) ],
        responses=UserProfileEditSerializer )
    def get (this, request):
        serializer_data = { key: request.GET.get (key) for key in ['nickname', 'avatar_name', 'background_color_id'] }

        serializer = UserProfileEditSerializer (data=serializer_data, context={'user': request.user.user_profile})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)


class UserDeleteAccountView(ActiveAPIUserView):
    @extend_schema(description="Deletes all user data", responses=UserAccountDeleteSerializer)
    def get(self, request):
        serializer = UserAccountDeleteSerializer()
        serializer.delete(request.user)
        return APIResponse(status=status.HTTP_200_OK)
