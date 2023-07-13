from api.rest_auth.views import ActiveAPIUserView
from api.users.models import UserObstacleActivityRecordInterval
from api.users.serializers import ObstacleActivityRecordSerializer

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from rest_framework.response import Response as APIResponse


__all__ = ['TeamObstacleActivityRecordView']


class TeamObstacleActivityRecordView(ActiveAPIUserView):
    @extend_schema(
        parameters=[
            OpenApiParameter (
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='interval',
                type={'enum': UserObstacleActivityRecordInterval.names},
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter(
                name='team_uid',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True),
        ],
        responses=ObstacleActivityRecordSerializer)
    def get(self, request):
        serializer_data = {key: request.GET.get(key) for key in ['start_date', 'end_date', 'interval']}
        team_uid = request.GET.get ('team_uid')
        serializer_context = {'user': request.user.user_profile, 'team_uid': team_uid}

        serializer = ObstacleActivityRecordSerializer(data=serializer_data, context=serializer_context)
        serializer.is_valid(raise_exception=True)

        return APIResponse(serializer.validated_data)
