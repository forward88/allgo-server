from functools import reduce
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from django.contrib.postgres.fields import DateTimeRangeField

from . import ObstacleActivityWindow, UserChallengeAction

__all__ = ['UserChallengePhase']

class UserChallengePhase (models.Model):
    user_challenge = models.ForeignKey ('users.UserChallenge', on_delete=models.CASCADE, related_name='phases')
    span = DateTimeRangeField ()
    start_action = models.CharField (max_length=1, choices=UserChallengeAction.choices)
    end_action = models.CharField (max_length=1, choices=UserChallengeAction.choices)

    def split (this, action):
        now = timezone.now ()

        with transaction.atomic ():
            this.span = (this.span.lower, now)
            this.end_action = action
            this.save ()

            if action == UserChallengeAction.PAUSE:
                end_datetime = None
                next_end_action = UserChallengeAction.PAUSE
                active = False
            else:
                end_datetime = now + (this.user_challenge.challenge.duration - this.user_challenge.elapsed_duration)
                next_end_action = UserChallengeAction.EXPIRE
                active = True

            next_phase = UserChallengePhase (
                user_challenge = this.user_challenge,
                span = (now, end_datetime),
                start_action = action,
                end_action = next_end_action)
            next_phase.save ()

            if action == UserChallengeAction.PAUSE:
                current_obstacle_phase = this.obstacle_windows.get (span__contains=now)
                current_obstacle_phase.split (next_phase)

                for span in this.obstacle_windows.filter (span__startswith__gt=timezone.now ()):
                    span.challenge_phase = next_phase
                    span.save ()
            else:
                phase_shift = this.span [1] - this.span [0]

                for phase in this.obstacle_windows.all ():
                    phase.challenge_phase = next_phase
                    phase.span = (phase.span.lower + phase_shift, phase.span.upper + phase_shift)
                    phase.save ()

        return next_phase

    def terminate (this, action):
        now = timezone.now ()

        with transaction.atomic ():
            this.span = (this.span.lower, now)
            this.end_action = action
            this.save ()

            obstacle_windows = this.obstacle_windows.filter (span__contains=now)
            if len (obstacle_windows) > 0:
                obstacle_windows [0].span = (obstacle_windows [0].span.lower, now)
                obstacle_windows [0].save ()
