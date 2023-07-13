from datetime import timedelta

from django.db import models
from django.contrib import admin

__all__ = ['ObstacleTask', 'Obstacle']

class ObstacleTask (models.Model):
    singular_name = models.CharField (max_length=1024, verbose_name='Singular Name')
    plural_name = models.CharField (max_length=1024, verbose_name='Plural Name')
    discrete = models.BooleanField (default=True)

    class Meta:
        verbose_name = "Obstacle Task"

    def __str__ (this):
        return this.plural_name

class Obstacle (models.Model):
    class ObstacleInterval (models.TextChoices):
        DAILY = ('D', 'Daily')
        WEEKLY = ('W', 'Weekly')
        MONTHLY = ('M', 'Monthly')

    challenge = models.ForeignKey ('Challenge', on_delete=models.CASCADE, related_name='obstacles')
    task = models.ForeignKey ('ObstacleTask', on_delete=models.CASCADE)
    interval = models.CharField (max_length=1, choices=ObstacleInterval.choices)
    sequence_rank = models.PositiveSmallIntegerField (null=True, blank=True, default=None)
    threshold = models.DecimalField (max_digits=16, decimal_places=3)
    subcategory = models.ForeignKey ('ChallengeCategory', on_delete=models.PROTECT, null=True, blank=True, help_text="Subcategory only pertinant for Mixed challenges")

    @property
    def interval_type_name (this):
        return this.ObstacleInterval (this.interval).name

    @property
    def duration_days (this):
        if this.interval == Obstacle.ObstacleInterval.DAILY:
            return 1
        if this.interval == Obstacle.ObstacleInterval.WEEKLY:
            return 7
        return 28

    @property
    def duration (this):
        return timedelta (days=this.duration_days)

    @property
    def duration_seconds (this):
        return this.duration.total_seconds ()

    @property
    def repeated (this):
        return this.sequence_rank == None

    @property
    def threshold_trimmed (this):
        if this.threshold == this.threshold.to_integral ():
            return this.threshold.quantize (1)

        return this.threshold.normalize ()

    @property
    def discrete (this):
        return this.task.discrete

    def __str__ (this):
        if this.threshold == 1:
            return f"{this.threshold_trimmed} {this.task.singular_name}"

        return f"{this.threshold_trimmed} {this.task.plural_name}"
