from django.db import models, transaction
from django.utils import timezone
from django.contrib.postgres.fields import DateTimeRangeField

__all__ = ['ObstacleActivityWindow']

class ObstacleActivityWindow (models.Model):
    challenge_phase = models.ForeignKey ('users.UserChallengePhase', on_delete=models.CASCADE, related_name='obstacle_windows')
    span = DateTimeRangeField ()
    sequence_rank = models.PositiveSmallIntegerField ()

    @property
    def obstacle (this):
        return this.challenge_phase.user_challenge.challenge.obstacles_in_sequence [this.sequence_rank - 1]

    @property
    def elapsed_duration (this):
        return UserObstacleActivityPhase.objects \
            .filter (challenge_phase=this.challenge_phase, phase__lte=timezone.now ()) \
            .aggregate (
                elapsed_duration=models.Sum (models.functions.Least (models.Value (timezone.now ()), models.F ('phase__endswith')) - models.F ('phase__startswith'))) ['elapsed_duration']

    def split (this, next_challenge_phase):
        now = timezone.now ()

        with transaction.atomic ():
            span_end = this.span.upper

            this.span = (this.span.lower, now)
            this.save ()

            next_phase = ObstacleActivityWindow (
                challenge_phase = next_challenge_phase,
                span = (now, span_end),
                sequence_rank = this.sequence_rank)
            next_phase.save ()

        return next_phase
