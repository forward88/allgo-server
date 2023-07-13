from datetime import timedelta

from django.db import models
from django.core import exceptions
from django.utils import timezone

from . import BaseEvent
from api.users.models import ObstacleActivityWindow

__all__ = ['ObstacleRequiresDiscreteAmount', 'InvalidObstacleException', 'calculate_registered_amount', 'ObstacleActivityEvent']

class ObstacleRequiresDiscreteAmount (exceptions.BadRequest):
    pass

class InvalidObstacleException (exceptions.BadRequest):
    pass

def calculate_registered_amount (amount, amount_completed, threshold):
    if amount < 0:
        return max (amount, -amount_completed)
    else:
        return min (amount, threshold - amount_completed)

class ObstacleActivityEventManager (models.Manager):
    def add_event (this, user, obstacle, sequence_rank, amount):
        if obstacle.task.discrete and amount != int (amount):
            raise ObstacleRequiresDiscreteAmount ()

        now = timezone.now ()
        window = ObstacleActivityWindow.objects.filter (
            challenge_phase__user_challenge__user=user,
            sequence_rank=sequence_rank,
            challenge_phase__user_challenge__challenge=obstacle.challenge,
            span__contains=now).first ()

        if window is None:
            raise InvalidObstacleException ()

        for active_user_obstacle in user.current_obstacles:
            if active_user_obstacle.obstacle.pk == obstacle.pk and active_user_obstacle.sequence_rank == sequence_rank:
                user_obstacle = active_user_obstacle
                break

        amount_registered = calculate_registered_amount (amount, user_obstacle.amount_completed, user_obstacle.obstacle.threshold)

        streak = 1

        yesterday = timezone.now () - timedelta (days=1)
        yesterday_event = ObstacleActivityEvent.objects.filter (
            api_user=user.api_user,
            ctime__year=yesterday.year,
            ctime__month=yesterday.month,
            ctime__day=yesterday.day).first ()

        if yesterday_event is not None:
            streak += yesterday_event.streak

        event = this.model(
            api_user=user.api_user,
            obstacle_window=window,
            amount_registered=amount_registered,
            streak=streak,
        )
        event.save ()

        return event

class ObstacleActivityEvent (BaseEvent):
    obstacle_window = models.ForeignKey ('users.ObstacleActivityWindow', on_delete=models.CASCADE, related_name='obstacle_activity_events')
    amount_registered = models.DecimalField (max_digits=16, decimal_places=3, default=0)
    streak = models.PositiveIntegerField(default=0)

    objects = ObstacleActivityEventManager ()

    @property
    def xp_earned(self):
        return self.amount_registered * self.obstacle_window.obstacle.challenge.base_xp_unit
