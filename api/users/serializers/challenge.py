import enum

from django.core import exceptions as django_exceptions
from rest_framework import serializers, exceptions as rf_exceptions

from api.users.models import UserChallenge, UserChallengeAction
from api.challenges.models import Challenge
from api.users.serializers.obstacle import NestedUserObstacleSerializer
from api.challenges.serializers import NestedChallengeSerializer

__all__ = ['UserChallengeSerializer', 'UserChallengeListSerializer', 'UserChallengeActionSerializer']

class UserChallengeSerializer (serializers.ModelSerializer):
    class Meta:
        model = UserChallenge
        fields = ['challenge', 'iteration', 'state', 'remaining_seconds', 'remaining_days', 'obstacles', 'xp_earned']

    challenge = NestedChallengeSerializer (many=False)
    state = serializers.CharField (source='state_name')
    remaining_seconds = serializers.IntegerField ()
    remaining_days = serializers.IntegerField ()
    obstacles = NestedUserObstacleSerializer (many=True, source='user_obstacles')

class NestedUserChallengeSerializer (UserChallengeSerializer):
    class Meta (UserChallengeSerializer.Meta):
        fields = [ f for f in UserChallengeSerializer.Meta.fields if f != 'obstacles' ]

class UserChallengeListSerializer (serializers.Serializer):
    open_challenges = NestedUserChallengeSerializer (many=True)
    closed_challenges = NestedUserChallengeSerializer (many=True)

class UserChallengeBaseSerializer (serializers.Serializer):
    challenge_id = serializers.IntegerField (write_only=True)

    def validate_challenge_id (this, challenge_id):
        try:
            this.context ['challenge'] = Challenge.objects.get (pk=challenge_id)
        except Challenge.DoesNotExist:
            raise rf_exceptions.NotFound (detail=f"Challenge<pk={challenge_id}> does not exist")

        return challenge_id

class UserChallengeActionSerializer (UserChallengeBaseSerializer):
    action = serializers.ChoiceField (UserChallengeAction.client_actions, write_only=True)
    iteration = serializers.IntegerField (read_only=True)

    def validate (this, data):
        user = this.context ['user']
        challenge = this.context ['challenge']
        action = getattr (UserChallengeAction, data ['action'])

        phase = user.do_challenge_action (challenge, action)

        return {'iteration': phase.iteration}
