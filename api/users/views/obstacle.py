import enum
from decimal import Decimal

from rest_framework.response import Response as APIResponse
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.rest_auth.views import ActiveAPIUserView
from api.challenges.models import Obstacle
from api.users.models import UserObstacleActivityRecordInterval
from api.users.serializers import UserObstacleListSerializer, AddObstacleActivitySerializer, ObstacleActivityRecordSerializer
from api.events.models import ObstacleRequiresDiscreteAmount, InvalidObstacleException

__all__ = ['AddObstacleActivityErrorMessage', 'UserObstacleListView', 'AddObstacleActivityView', 'ObstacleActivityRecordView']

class AddObstacleActivityErrorMessage (enum.Enum):
    INVALID_OBSTACLE = "Invalid obstacle and sequence_rank for user"
    MISAPPLIED_FLOAT_AMOUNT = "Obstacle does not support non-integer performance amounts"

class UserObstacleListView (ActiveAPIUserView):
    @extend_schema (
        parameters= [
            OpenApiParameter (
                name='as_of',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False) ],
        responses=UserObstacleListSerializer)
    def get (this, request):
        serializer_data = {'as_of': request.GET.get ('as_of')}
        serializer_context = {'user': request.user.user_profile}

        serializer = UserObstacleListSerializer (data=serializer_data, context=serializer_context)
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class AddObstacleActivityView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='obstacle_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='sequence_rank',
                type=int,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='amount',
                type=Decimal,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=AddObstacleActivitySerializer)
    def get (this, request):
        serializer_data = { key: request.GET.get (key) for key in ['obstacle_id', 'sequence_rank', 'amount'] }
        serializer_context = {'user': request.user.user_profile}

        serializer = AddObstacleActivitySerializer (data=serializer_data, context=serializer_context)

        try:
            serializer.is_valid (raise_exception=True)
        except ObstacleRequiresDiscreteAmount:
            raise serializers.ValidationError (detail=AddObstacleActivityErrorMessage.MISAPPLIED_FLOAT_AMOUNT.value)
        except InvalidObstacleException:
            raise serializers.ValidationError (detail=AddObstacleActivityErrorMessage.INVALID_OBSTACLE.value)

        return APIResponse (serializer.validated_data)

class ObstacleActivityRecordView (ActiveAPIUserView):
    @extend_schema (
        parameters= [
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
                required=True) ],
        responses=ObstacleActivityRecordSerializer)
    def get (this, request):
        serializer_data = { key: request.GET.get (key) for key in ['start_date', 'end_date', 'interval'] }
        serializer_context = {'user': request.user.user_profile}

        serializer = ObstacleActivityRecordSerializer (data=serializer_data, context=serializer_context)
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)
