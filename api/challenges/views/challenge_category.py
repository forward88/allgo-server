from rest_framework.response import Response as APIResponse
from drf_spectacular.utils import extend_schema

from ..models import ChallengeCategory
from ..serializers import ChallengeCategoryListSerializer
from ...rest_auth.views import AnonymousAPIUserView

class ChallengeCategoryListView (AnonymousAPIUserView):
    @extend_schema (responses=ChallengeCategoryListSerializer (many=True))
    def get (this, request):
        categories = ChallengeCategory.objects.all ()
        serializer = ChallengeCategoryListSerializer (categories, many=True)

        return APIResponse (serializer.data)
