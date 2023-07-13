from rest_framework import serializers

from ..models import Achievement

class AchievementSerializer (serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['name', 'color_image_src', 'grey_image_src']

    color_image_src = serializers.CharField ()
    grey_image_src = serializers.CharField ()
