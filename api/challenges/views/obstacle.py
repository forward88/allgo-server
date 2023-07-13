from rest_framework.response import Response as APIResponse
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import Obstacle
from ..serializers import ObstacleSerializer
from ...rest_auth.views import AnonymousAPIUserView

class ObstacleDetailView (AnonymousAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='obstacle_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=ObstacleSerializer)
    def get (this, request, obstacle_id=None):
        obstacle_id = request.GET.get ('obstacle_id')

        try:
            obstacle = Obstacle.objects.get (pk=obstacle_id)
        except Obstacle.DoesNotExist:
            raise NotFound (detail=f"Obstacle<pk={obstacle_id}> does not exist")

        serializer = ObstacleSerializer (obstacle, context={'request': request})

        return APIResponse (serializer.data)
