from rest_framework import serializers
from rest_framework import exceptions

from api.users.models import UserObstacleActivityRecordInterval, UserObstacle
from api.challenges.models import Obstacle
from api.challenges.serializers import ObstacleSerializer, NestedChallengeSerializer
from api.teams.models import Team

__all__ = ['UserObstacleListSerializer', 'AddObstacleActivitySerializer', 'ObstacleActivityRecordSerializer']

class UserObstacleSerializer (serializers.ModelSerializer):
    class Meta:
        model = UserObstacle
        fields = ['challenge', 'obstacle', 'sequence_rank', 'amount_completed', 'remaining_seconds', 'remaining_days', 'start_date', 'end_date']

    challenge = NestedChallengeSerializer (many=False)
    obstacle = ObstacleSerializer (many=False)
    remaining_seconds = serializers.IntegerField ()
    remaining_days = serializers.IntegerField ()
    start_date = serializers.DateField ()
    end_date = serializers.DateField ()

class NestedUserObstacleSerializer (UserObstacleSerializer):
    class Meta (UserObstacleSerializer.Meta):
        fields = [ f for f in UserObstacleSerializer.Meta.fields if f != 'challenge' ]

class UserObstacleListSerializer (serializers.Serializer):
    def get_fields (this):
        fields = super ().get_fields ()

        fields ['as_of'] = serializers.DateField (write_only=True, allow_null=True)
        fields [Obstacle.ObstacleInterval.DAILY.name] = serializers.ListField (read_only=True, child=UserObstacleSerializer (many=False))
        fields [Obstacle.ObstacleInterval.WEEKLY.name] = serializers.ListField (read_only=True, child=UserObstacleSerializer (many=False))
        fields [Obstacle.ObstacleInterval.MONTHLY.name] = serializers.ListField (read_only=True, child=UserObstacleSerializer (many=False))

        return fields

    def validate (this, data):
        user = this.context ['user']
        as_of = data ['as_of']

        obstacle_lists = {
            Obstacle.ObstacleInterval.DAILY.name: [],
            Obstacle.ObstacleInterval.WEEKLY.name: [],
            Obstacle.ObstacleInterval.MONTHLY.name: [] }

        for obstacle_data in user.get_obstacles (as_of=as_of):
            obstacle_lists [obstacle_data.obstacle.interval_type_name].append (UserObstacleSerializer (obstacle_data).data)

        return obstacle_lists

class AddObstacleActivitySerializer (serializers.Serializer):
    obstacle_id = serializers.IntegerField ()
    sequence_rank = serializers.IntegerField ()
    amount = serializers.DecimalField (
        max_digits=Obstacle._meta.get_field ('threshold').max_digits,
        decimal_places=Obstacle._meta.get_field ('threshold').decimal_places)
    amount_registered = serializers.DecimalField (
        read_only=True,
        max_digits=Obstacle._meta.get_field ('threshold').max_digits,
        decimal_places=Obstacle._meta.get_field ('threshold').decimal_places)

    def validate_obstacle_id (this, value):
        this.context ['obstacle'] = Obstacle.objects.get (pk=value)

        return value

    def validate (this, data):
        user = this.context ['user']
        obstacle = this.context ['obstacle']
        challenge = obstacle.challenge

        amount_registered = user.do_obstacle_activity (obstacle, data ['sequence_rank'], data ['amount']).amount_registered

        return {'amount_registered': amount_registered}


class UserObstacleActivityRecordDataSerializer (serializers.Serializer):
    start_date = serializers.DateField ()
    end_date = serializers.DateField ()
    amount_completed = serializers.DecimalField (
        max_digits=Obstacle._meta.get_field ('threshold').max_digits,
        decimal_places=Obstacle._meta.get_field ('threshold').decimal_places)
    amount_possible = serializers.DecimalField (
        max_digits=Obstacle._meta.get_field ('threshold').max_digits,
        decimal_places=Obstacle._meta.get_field ('threshold').decimal_places)

class UserObstacleActivityRecordSummarySerializer (serializers.Serializer):
    partitions = UserObstacleActivityRecordDataSerializer (many=True)
    average_amount_completed = serializers.DecimalField (
        max_digits=Obstacle._meta.get_field ('threshold').max_digits,
        decimal_places=Obstacle._meta.get_field ('threshold').decimal_places)
    max_streak = serializers.IntegerField ()
    n_obstacles = serializers.IntegerField ()
    total_xp_earned = serializers.IntegerField ()

class ObstacleActivityRecordSerializer (serializers.Serializer):
    start_date = serializers.DateField (write_only=True)
    end_date = serializers.DateField (write_only=True)
    interval = serializers.ChoiceField (UserObstacleActivityRecordInterval.names, write_only=True)
    activity_record = UserObstacleActivityRecordSummarySerializer (many=False, read_only=True)

    def validate_interval (this, value):
        return getattr (UserObstacleActivityRecordInterval, value)

    def validate(this, data):
        user = this.context ['user']
        team_uid = this.context.get('team_uid')

        if team_uid is None:
            record = user.get_obstacle_activity_record(data['start_date'], data['end_date'], data['interval'])
            return {'activity_record': UserObstacleActivityRecordSummarySerializer(record).data}

        else:
            try:
                team = Team.objects.get(shareable_uid=team_uid)
            except Team.DoesNotExist:
                raise exceptions.NotFound(detail=f"Team does not exist with given team_uid: {team_uid}")

            record = user.get_obstacle_activity_record(data['start_date'], data['end_date'], data['interval'], team=team)

        return {'activity_record': UserObstacleActivityRecordSummarySerializer(record).data}
