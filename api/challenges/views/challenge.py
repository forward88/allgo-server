from rest_framework.response import Response as APIResponse
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import Challenge
from ..serializers import ChallengeListSerializer, ChallengeDetailSerializer
from ...rest_auth.views import AnonymousAPIUserView

class ChallengeListView (AnonymousAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='name_pattern',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='A case-insensitive string-searching pattern applied to the `name` field of each `challenge` object.'),
            OpenApiParameter (
                name='category_ids',
                type={'type': 'array', 'items': {'type': 'integer'}},
                location=OpenApiParameter.QUERY,
                required=False,
                description='A comma-separated list of `category` IDs.',
                style='simple') ],
        responses=ChallengeListSerializer (many=True))
    def get (this, request):
        category_ids = request.GET.get ('category_ids')
        name_pattern = request.GET.get ('name_pattern')

        filter_kwargs = {}

        if category_ids is not None:
            filter_kwargs ['category_id__in'] = category_ids.split (',')
        if name_pattern is not None:
            filter_kwargs ['name__icontains'] = name_pattern

        if len (filter_kwargs) > 0:
            challenges = Challenge.objects.filter (**filter_kwargs)
        else:
            challenges = Challenge.objects.all ()

        serializer = ChallengeListSerializer (challenges, many=True, context={'request': request})

        return APIResponse (serializer.data)

class ChallengeDetailView (AnonymousAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='challenge_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=ChallengeDetailSerializer)
    def get (this, request, challenge_id=None):
        challenge_id = request.GET.get ('challenge_id')

        try:
            challenge = Challenge.objects.get (pk=challenge_id)
        except Challenge.DoesNotExist:
            raise NotFound (detail=f"Challenge<pk={challenge_id}> does not exist")

        serializer = ChallengeDetailSerializer (challenge, context={'request': request})

        return APIResponse (serializer.data)
