from datetime import timedelta

from django.db import models
from django.core import exceptions
from django.utils import timezone
from django.db.models import Max
from django.contrib.postgres.aggregates import ArrayAgg

from . import BaseEvent

__all__ = ['ChallengeState', 'ChallengeAction', 'ChallengeEvent']

class ChallengeState (models.TextChoices):
    ACTIVE = ('A', 'Active')
    PAUSED = ('P', 'Paused')
    COMPLETED = ('C', 'Completed')
    LEFT = ('L', 'Left')
    EXPIRED = ('E', 'Expired')

    @property
    def open (this):
        return this.name in ['ACTIVE', 'PAUSED']

    @property
    def closed (this):
        return not this.open

class ChallengeAction (models.TextChoices):
    JOIN = ('J', 'Join')
    PAUSE = ('P', 'Pause')
    UNPAUSE = ('U', 'Unpause')
    LEAVE = ('L', 'Leave')
    COMPLETE = ('C', 'Complete')
    EXPIRE = ('E', 'Expire')

    __past_tenses__ = {
        'JOIN': 'joined',
        'PAUSE': 'paused',
        'UNPAUSE': 'unpaused',
        'LEAVE': 'left',
        'COMPLETE': 'completed',
        'EXPIRE': 'expired' }

    __corresponding_states__ = {
        'JOIN': ChallengeState.ACTIVE,
        'PAUSE': ChallengeState.PAUSED,
        'UNPAUSE': ChallengeState.ACTIVE,
        'LEAVE': ChallengeState.LEFT,
        'COMPLETE': ChallengeState.COMPLETED,
        'EXPIRE': ChallengeState.EXPIRED }

    @property
    def past_tense (this):
        return this.__past_tenses__ [this.name]

    @property
    def state (this):
        return this.__corresponding_states__ [this.name]

class InvalidChallengeEventException (exceptions.BadRequest):
    def __init__ (this, action, previous_action):
        this.action = action
        this.previous_action = previous_action

class NullChallengeEvent:
    action = None
    iteration = 0

class ChallengeEventManager (models.Manager):
    __invalid_transitions__ = {
        # key: last action; value: invalid next actions
        None: [ChallengeAction.PAUSE, ChallengeAction.UNPAUSE, ChallengeAction.LEAVE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE],
        ChallengeAction.JOIN: [ChallengeAction.JOIN, ChallengeAction.UNPAUSE],
        ChallengeAction.PAUSE: [ChallengeAction.JOIN, ChallengeAction.PAUSE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE],
        ChallengeAction.UNPAUSE: [ChallengeAction.JOIN, ChallengeAction.UNPAUSE],
        ChallengeAction.LEAVE: [ChallengeAction.PAUSE, ChallengeAction.UNPAUSE, ChallengeAction.LEAVE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE],
        ChallengeAction.COMPLETE: [ChallengeAction.PAUSE, ChallengeAction.UNPAUSE, ChallengeAction.LEAVE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE],
        ChallengeAction.EXPIRE: [ChallengeAction.PAUSE, ChallengeAction.UNPAUSE, ChallengeAction.LEAVE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE] }

    def count_challenge_participants (this, challenge):
        return this.filter (challenge=challenge).distinct ('api_user').count ()

    def get_last_event (this, user, challenge, as_of=None):
        filter_kwargs = {'api_user': user.api_user, 'challenge': challenge}

        if as_of is not None:
            filter_kwargs ['ctime__lte'] = as_of
        else:
            as_of = timezone.now ()

        last_event = this.filter (**filter_kwargs).order_by ('ctime').last ()

        if last_event is None:
            last_event = NullChallengeEvent ()
        else:
            projected_expiration = last_event.projected_expiration

            if projected_expiration is not None and as_of > projected_expiration:
                last_event = this.model (
                    api_user=user.api_user,
                    ctime=projected_expiration,
                    challenge=challenge,
                    action=ChallengeAction.EXPIRE,
                    accumulated_time=challenge.duration,
                    iteration=last_event.iteration )

                last_event.save ()

        return last_event

    def add_event (this, user, challenge, action):
        last_event = this.get_last_event (user, challenge)

        if action in this.__invalid_transitions__ [last_event.action]:
            raise InvalidChallengeEventException (action, last_event.action)

        event = this.model (api_user=user.api_user, challenge=challenge, action=action, iteration=last_event.iteration)

        if action == ChallengeAction.JOIN:
            event.accumulated_time = timedelta (0)
            event.iteration = last_event.iteration + 1
        elif action in [ChallengeAction.PAUSE, ChallengeAction.COMPLETE] or (action == ChallengeAction.LEAVE and last_event.action != ChallengeAction.PAUSE):
            event.accumulated_time = last_event.accumulated_time + (timezone.now () - last_event.ctime)
        else:
            event.accumulated_time = last_event.accumulated_time

        event.save ()

        return event

class ChallengeEvent (BaseEvent):
    challenge = models.ForeignKey ('challenges.Challenge', on_delete=models.CASCADE, related_name='challenge_event_set')
    action = models.CharField (max_length=1, choices=ChallengeAction.choices)
    accumulated_time = models.DurationField (default=timedelta (0))
    iteration = models.PositiveSmallIntegerField ()

    objects = ChallengeEventManager ()

    class Meta:
        verbose_name = "Challenge Event"

    @property
    def projected_expiration (this):
        if this.action in [ChallengeAction.JOIN, ChallengeAction.UNPAUSE]:
            return this.ctime + (this.challenge.duration - this.accumulated_time)
        return None

    def get_elapsed_duration (this, as_of=None):
        elapsed_time = this.accumulated_time

        if this.action in [ChallengeAction.JOIN, ChallengeAction.UNPAUSE]:
            if as_of is None:
                as_of = timezone.now ()

            elapsed_time += as_of - this.ctime

        return min (elapsed_time, this.challenge.duration)

    def get_remaining_duration (this, as_of=None):
        if this.action in [ChallengeAction.LEAVE, ChallengeAction.COMPLETE, ChallengeAction.EXPIRE]:
            return timedelta (0)

        return this.challenge.duration - this.get_elapsed_duration (as_of=as_of)

    def __str__ (this):
        return f"{this.api_user.user_profile.nickname} {ChallengeAction (this.action).past_tense} {this.challenge.name} [{this.iteration}]"
