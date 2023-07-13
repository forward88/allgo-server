import itertools
from datetime import timedelta

from django.db import models, transaction
from django.core import exceptions
from django.utils import timezone
from django.contrib import admin
from django.apps import apps

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from schoolyard.settings import DAY_S
from . import UserChallengeAction, UserChallengePhase, ObstacleActivityWindow

from services import Sendbird

__all__ = ['InvalidUserChallengeActionException', 'calculate_remaining_days', 'UserChallenge']

class InvalidUserChallengeActionException (exceptions.BadRequest):
    def __init__ (this, action, previous_action):
        this.action = action
        this.previous_action = previous_action

class UserChallengeManager (models.Manager):
    __invalid_transitions__ = {
        # key: last action; value: invalid next actions
        None: [UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE, UserChallengeAction.LEAVE, UserChallengeAction.COMPLETE, UserChallengeAction.EXPIRE],
        UserChallengeAction.JOIN: [UserChallengeAction.JOIN, UserChallengeAction.UNPAUSE],
        UserChallengeAction.PAUSE: [UserChallengeAction.JOIN, UserChallengeAction.PAUSE, UserChallengeAction.COMPLETE, UserChallengeAction.EXPIRE],
        UserChallengeAction.UNPAUSE: [UserChallengeAction.JOIN, UserChallengeAction.UNPAUSE],
        UserChallengeAction.LEAVE: [UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE, UserChallengeAction.LEAVE, UserChallengeAction.COMPLETE, UserChallengeAction.EXPIRE],
        UserChallengeAction.COMPLETE: [UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE, UserChallengeAction.LEAVE, UserChallengeAction.COMPLETE, UserChallengeAction.EXPIRE],
        UserChallengeAction.EXPIRE: [UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE, UserChallengeAction.LEAVE, UserChallengeAction.COMPLETE, UserChallengeAction.EXPIRE] }

    def create (this, user, challenge, iteration):
        with transaction.atomic ():
            now = timezone.now ()

            user_challenge = this.model (user=user, challenge=challenge, iteration=iteration)
            user_challenge.save ()

            initial_phase = UserChallengePhase (
                user_challenge = user_challenge,
                span = (now, now + challenge.duration),
                start_action = UserChallengeAction.JOIN,
                end_action = UserChallengeAction.EXPIRE)
            initial_phase.save ()

            for (i, obstacle) in zip (itertools.count (), challenge.obstacles_in_sequence):
                obstacle_phase = ObstacleActivityWindow (
                    challenge_phase = initial_phase,
                    span = (now + i * challenge.obstacle_duration, now + (i + 1) * challenge.obstacle_duration),
                    sequence_rank = i + 1)
                obstacle_phase.save ()

        return user_challenge

    def do_action (this, user, challenge, action):
        latest_user_challenge = this.filter (user=user, challenge=challenge).order_by ('iteration').last ()

        if latest_user_challenge is None:
            current_phase = None
        else:
            current_phase = latest_user_challenge.current_phase

        if current_phase is None:
            last_action = None
            current_iteration = latest_user_challenge.iteration + 1 if latest_user_challenge is not None else 1
        else:
            last_action = current_phase.start_action
            current_iteration = latest_user_challenge.iteration

        if action in this.__invalid_transitions__ [last_action]:
            raise InvalidUserChallengeActionException (UserChallengeAction (action), UserChallengeAction (last_action) if last_action is not None else None)

        if action == UserChallengeAction.JOIN:
            with transaction.atomic():
                latest_user_challenge = this.create (user, challenge, current_iteration)

                if Sendbird.get_channel (challenge.chat_channel_id) is None:
                    Sendbird.create_channel (challenge.chat_channel_id, [user.chat_user_id])

                Sendbird.join_channel (challenge.chat_channel_id, user.chat_user_id)

        elif action in [UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE]:
            current_phase.split (action)

        elif action in [UserChallengeAction.LEAVE, UserChallengeAction.COMPLETE]:
            current_phase.terminate (action)

        else:
            pass

        return latest_user_challenge

def calculate_remaining_days (remaining_duration):
    return remaining_duration.days + round (remaining_duration.seconds / DAY_S)

class UserChallenge (models.Model):
    user = models.ForeignKey ('users.UserProfile', on_delete=models.CASCADE, related_name='user_challenges')
    challenge = models.ForeignKey ('challenges.Challenge', on_delete=models.CASCADE, related_name='user_challenges')
    iteration = models.PositiveSmallIntegerField ()

    objects = UserChallengeManager ()

    class Meta:
        verbose_name = 'User Challenge'
        unique_together = ['user', 'challenge', 'iteration']

    @property
    @extend_schema_field (serializers.DecimalField (max_digits=16, decimal_places=3))
    def xp_earned (this):
        return this.user_obstacles.aggregate (total_xp_earned=models.Sum ('xp_earned')) ['total_xp_earned']

    @property
    def current_phase (this):
        return this.phases.filter (span__contains=timezone.now ()).first ()

    @property
    def active (this):
        current_phase = this.current_phase
        return current_phase is not None and current_phase.start_action != UserChallengeAction.PAUSE

    @property
    def open (this):
        return this.current_phase is not None

    @property
    def closed (this):
        return not this.open

    @property
    def state (this):
        now = timezone.now ()

        last_phase = this.phases.filter (span__startswith__lte=now).order_by ('span').last ()

        if last_phase.span.upper is None or last_phase.span.upper > now:
            last_action = last_phase.start_action
        else:
            last_action = last_phase.end_action

        return UserChallengeAction (last_action).state

    @property
    def state_name (this):
        return this.state.name

    @property
    @admin.display (description='State')
    def state_label (this):
        return this.state.label

    @property
    def elapsed_duration (this):
        return this.phases \
            .filter (~models.Q (start_action=UserChallengeAction.PAUSE.value)) \
            .aggregate (
                elapsed_duration=models.Sum (models.functions.Least (models.Value (timezone.now ()), models.F ('span__endswith')) - models.F ('span__startswith'))) ['elapsed_duration']

    @property
    def remaining_duration (this):
        if this.closed:
            return timedelta (0)

        return this.challenge.duration - this.elapsed_duration

    @property
    def remaining_seconds (this):
        return this.remaining_duration.total_seconds ()

    @property
    def remaining_days (this):
        return calculate_remaining_days (this.remaining_duration)

    @property
    def completable (this):
        event_model = apps.get_model ('events', 'ObstacleActivityEvent')
        event_summaries = event_model.objects.values ('obstacle_window__sequence_rank').filter (obstacle_window__challenge_phase__user_challenge=this).annotate (total_amount=models.Sum ('amount_registered'))

        obstacle_totals = {}
        for event_summary in event_summaries:
            obstacle_totals [event_summary ['obstacle_window__sequence_rank']] = event_summary ['total_amount']

        for (i, obstacle) in zip (itertools.count (), this.challenge.obstacles_in_sequence):
            obstacle_total = obstacle_totals.get (i + 1, 0)

        return False

    def __str__ (this):
        return f"{this.user.nickname} {this.challenge.name} [{this.iteration}]"
