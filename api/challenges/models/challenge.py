from django.db import models
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from api.users.models import UserChallengePhase
from services import Sendbird

class Challenge (models.Model):
    author = models.ForeignKey ('users.UserProfile', on_delete=models.PROTECT, related_name='+')
    category = models.ForeignKey ('ChallengeCategory', on_delete=models.PROTECT)
    name = models.CharField (max_length=1024)
    description = models.TextField ()
    duration = models.DurationField (help_text='Specify durations as such: "&lt;number&gt; days".')
    color_profile = models.ForeignKey ('ChallengeColorProfile', on_delete=models.PROTECT, verbose_name="Color Profile", help_text='The initial value is randomly selected.')
    xp_value = models.PositiveIntegerField (verbose_name="XP Value")
    external_url = models.URLField (max_length=1024, null=True, blank=True, default=None, verbose_name="External URL")
    ctime = models.DateTimeField (auto_now_add=True)

    @property
    def obstacle_duration (this):
        return this.obstacles.first ().duration

    @property
    def n_obstacles (this):
        return this.duration // this.obstacle_duration

    @property
    @admin.display (description="repeat obstacles")
    def repeated_obstacles (this):
        return this.obstacles.first ().repeated

    @property
    def obstacles_in_sequence (this):
        obstacles = list (this.obstacles.all ().order_by ('sequence_rank'))

        if obstacles [0].repeated:
            return [obstacles [0]] * (this.duration // obstacles [0].duration)

        return obstacles

    @property
    def threshold_sum (this):
        return this.scoring.threshold_sum

    @property
    def n_participants (this):
        return UserChallengePhase.objects.filter (user_challenge__challenge=this, span__contains=timezone.now ()).count ()

    @property
    def base_xp_unit (this):
        return this.scoring.xp_base_unit

    @property
    @admin.display (description="duration (d)")
    def duration_days (this):
        return this.duration.days

    @property
    def duration_seconds (this):
        return this.duration.total_seconds ()

    @property
    @admin.display (description="name")
    def title_block (this):
        style_block = (
            "display: inline-block; " +
            "width: 20em; " +
            "padding: 0.25em 1em; " +
            f"background-color: #{this.color_profile.background_rgb}; " +
            f"color: #{this.color_profile.title_rgb}; " +
            "text-align: left; " +
            "text-transform: uppercase; " +
            "font-weight: 900;")

        return format_html (f"<span style='{style_block}'>{this.name}</span>")

    @property
    @admin.display (description="category")
    def category_name (this):
        return this.category.name

    @property
    @extend_schema_field (serializers.CharField ())
    def chat_channel_id (this):
        return Sendbird.build_channel_url ('challenge', this.pk)

    def __str__ (self):
        return self.name
