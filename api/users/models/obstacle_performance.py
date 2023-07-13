from django.db import models, transaction
from django.db.models import F

from ...events.models import ObstaclePerformanceEvent

__all__ = ['ObstaclePerformance']

class ObstaclePerformance (models.Model):
    challenge_participation = models.ForeignKey ('ChallengeParticipation', on_delete=models.CASCADE, related_name='obstacle_performance_set')
    obstacle = models.ForeignKey ('challenges.Obstacle', on_delete=models.CASCADE, related_name='+')
    sequence_rank = models.PositiveSmallIntegerField ()
    amount = models.DecimalField (max_digits=16, decimal_places=3, default=0)

    @property
    def remaining_days (this):
        challenge_elapsed_days = this.challenge_participation.elapsed_days
        obstacle_interval = this.obstacle.interval_days

        interval_elapsed_days = challenge_elapsed_days % obstacle_interval

        if interval_elapsed_days == 0 and challenge_elapsed_days != 0:
            return 0

        return obstacle_interval - interval_elapsed_days

    def register_amount (this, amount):
        amount_registered = min (amount, this.obstacle.threshold - this.amount)

        if amount_registered > 0:
            with transaction.atomic ():
                this.amount = F ('amount') + amount_registered
                this.save ()

                event = ObstaclePerformanceEvent (
                    api_user=this.challenge_participation.participant.api_user,
                    obstacle_performance=this,
                    amount_registered=amount_registered)
                event.save ()

        return amount_registered
