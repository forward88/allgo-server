from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField

__all__ = ['UserObstacle']

from . import calculate_remaining_days

class UserObstacle (models.Model):
    user_obstacle_id = models.CharField (max_length=32, primary_key=True)
    user_challenge = models.ForeignKey ('users.UserChallenge', on_delete=models.DO_NOTHING, related_name='user_obstacles')
    challenge = models.ForeignKey ('challenges.Challenge', on_delete=models.DO_NOTHING, related_name='user_obstacles')
    iteration = models.PositiveSmallIntegerField ()
    obstacle = models.ForeignKey ('challenges.Obstacle', on_delete=models.DO_NOTHING, related_name='user_obstacles')
    sequence_rank = models.PositiveSmallIntegerField ()
    overall_span = DateTimeRangeField ()
    amount_completed = models.DecimalField (max_digits=16, decimal_places=3)
    xp_earned = models.DecimalField (max_digits=16, decimal_places=3)
    n_spans = models.PositiveSmallIntegerField ()

    class Meta:
        managed = False
        db_table = 'users_user_obstacle_view'

    @property
    def start_date (this):
        return this.overall_span.lower.date ()

    @property
    def end_date (this):
        return this.overall_span.upper.date ()

    @property
    def remaining_duration (this):
        return this.obstacle.duration - (this.user_challenge.elapsed_duration % this.obstacle.duration)

    @property
    def remaining_seconds (this):
        return this.remaining_duration.total_seconds ()

    @property
    def remaining_days (this):
        return calculate_remaining_days (this.remaining_duration)
