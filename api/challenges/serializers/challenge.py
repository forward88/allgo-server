from rest_framework import serializers

from ..models import Challenge, ChallengeColorProfile, Obstacle, ObstacleTask
from . import NestedChallengeCategorySerializer

__all__ = ['ObstacleTaskSerializer', 'ObstacleSerializer', 'ChallengeListSerializer', 'ChallengeDetailSerializer', 'NestedChallengeSerializer']

class ObstacleTaskSerializer (serializers.ModelSerializer):
    class Meta:
        model = ObstacleTask
        fields = ['singular_name', 'plural_name', 'discrete']

class ObstacleSerializer (serializers.ModelSerializer):
    class Meta:
        model = Obstacle
        fields = ['obstacle_id', 'interval_type', 'interval_days', 'duration_seconds', 'threshold', 'task', 'subcategory']

    obstacle_id = serializers.IntegerField (source='pk')
    interval_type = serializers.ChoiceField (Obstacle.ObstacleInterval.names, source='interval_type_name')
    interval_days = serializers.IntegerField (source='duration_days')
    task = ObstacleTaskSerializer (many=False)
    subcategory = NestedChallengeCategorySerializer (many=False)
    duration_seconds = serializers.IntegerField ()

class ChallengeListSerializer (serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['challenge_id', 'name', 'description', 'category', 'duration_seconds', 'duration_days', 'xp_value', 'n_participants']

    challenge_id = serializers.IntegerField (source='pk')
    category = NestedChallengeCategorySerializer (many=False)
    duration_seconds = serializers.IntegerField ()
    duration_days = serializers.IntegerField ()
    n_participants = serializers.IntegerField ()

class NestedChallengeColorProfileSerializer (serializers.ModelSerializer):
    class Meta:
        model = ChallengeColorProfile
        fields = ['background_rgb', 'title_rgb', 'description_rgb']

class ChallengeDetailSerializer (serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['challenge_id', 'name', 'description', 'category', 'obstacles', 'color_profile', 'duration_seconds', 'duration_days', 'xp_value', 'n_participants', 'external_url', 'chat_channel_id']

    challenge_id = serializers.IntegerField (source='pk')
    color_profile = NestedChallengeColorProfileSerializer (many=False)
    category = NestedChallengeCategorySerializer (many=False)
    obstacles = ObstacleSerializer (many=True)
    duration_seconds = serializers.IntegerField ()
    duration_days = serializers.IntegerField ()
    n_participants = serializers.IntegerField ()

class NestedChallengeSerializer (serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['challenge_id', 'name', 'description', 'category', 'xp_value', 'n_participants', 'chat_channel_id']

    challenge_id = serializers.IntegerField (source='pk')
    category = NestedChallengeCategorySerializer (many=False)
    n_participants = serializers.IntegerField ()
