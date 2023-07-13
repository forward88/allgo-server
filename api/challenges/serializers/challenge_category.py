from rest_framework import serializers

from ..models import ChallengeCategory

class ChallengeCategoryListSerializer (serializers.ModelSerializer):
    class Meta:
        model = ChallengeCategory
        fields = ['category_id', 'name', 'icon_emoji']

    category_id = serializers.IntegerField (source='pk')

class NestedChallengeCategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = ChallengeCategory
        fields = ['name', 'icon_emoji']
