import enum

from rest_framework import serializers
from rest_framework.response import Response as APIResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from ..models import UserChallengeAction, InvalidUserChallengeActionException
from ..serializers import UserChallengeSerializer, UserChallengeListSerializer, UserChallengeActionSerializer
from api.rest_auth.views import ActiveAPIUserView, LateralUserView
from api.challenges.models import Challenge

__all__ = ['UserChallengeViewErrorMessage', 'UserChallengeListView', 'UserChallengeDetailView', 'UserChallengeActionView']

class UserChallengeViewErrorMessage (enum.Enum):
    CHALLENGE_NOT_FOUND = "Challenge<pk={challenge_id}> does not exist"
    INVALID_CHALLENGE_ACTION = "Invalid action: {action} can't follow {previous_action}"

class UserChallengeListView (LateralUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False) ],
        responses=UserChallengeListSerializer)
    def get (this, request):
        challenge_lists = {
            'open_challenges': this.query_user.user_profile.open_challenges,
            'closed_challenges': this.query_user.user_profile.closed_challenges }

        serializer = UserChallengeListSerializer (challenge_lists)

        return APIResponse (serializer.data)

class UserChallengeDetailView (LateralUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False),
            OpenApiParameter (
                name='challenge_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=UserChallengeSerializer)
    def get (this, request):
        challenge = Challenge.objects.get (pk=request.GET.get ('challenge_id'))
        user_challenge = this.query_user.user_profile.get_user_challenge (challenge)

        serializer = UserChallengeSerializer (user_challenge)

        return APIResponse (serializer.data)

class UserChallengeActionView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='challenge_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='action',
                type={'enum': UserChallengeAction.client_actions},
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=UserChallengeActionSerializer)
    def get (this, request):
        data = {
            'challenge_id': request.GET.get ('challenge_id'),
            'action': request.GET.get ('action') }

        serializer = UserChallengeActionSerializer (data=data, context={'user': request.user.user_profile})

        try:
            serializer.is_valid (raise_exception=True)
        except Challenge.DoesNotExist:
            raise serializers.ValidationError (UserChallengeViewErrorMessage.CHALLENGE_NOT_FOUND.value.format (challenge_id=data ['challenge_id']))
        except InvalidUserChallengeActionException as e:
            action = e.action.name

            if e.previous_action is None:
                previous_action = None
            else:
                previous_action = e.previous_action.name

            raise serializers.ValidationError (UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action=action, previous_action=previous_action))

        return APIResponse (serializer.validated_data)
