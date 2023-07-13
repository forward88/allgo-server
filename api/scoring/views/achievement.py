from rest_framework.response import Response as APIResponse
from drf_spectacular.utils import extend_schema

from ..models import Achievement
from ..serializers import AchievementSerializer
from ...rest_auth.views import AnonymousAPIUserView

class AchievementListView (AnonymousAPIUserView):
    @extend_schema (responses=AchievementSerializer (many=True))
    def get (this, request):
        achievements = Achievement.objects.all ().order_by ('order_rank')
        serializer = AchievementSerializer (achievements, many=True)

        return APIResponse (serializer.data)
