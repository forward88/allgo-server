import random, string

from django.db import models

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from api.users.models import UserObstacle
from services import Sendbird

__all__ = ['Team']

def generate_shareable_uid ():
    return ''.join (random.choices (string.ascii_uppercase, k=8))

class Team (models.Model):
    shareable_uid = models.CharField (max_length=8, unique=True, default=generate_shareable_uid)
    creator = models.ForeignKey ('users.UserProfile', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='created_teams')
    user_created = models.BooleanField ()
    ctime = models.DateTimeField (auto_now_add=True, verbose_name="Created At")

    @property
    @extend_schema_field (serializers.DecimalField (max_digits=16, decimal_places=3))
    def xp_earned (this):
        return UserObstacle.objects.filter (user_challenge__user__in=this.members.all ()).aggregate (total_xp_earned=models.Sum ('xp_earned')) ['total_xp_earned']

    @property
    def creator_nickname (this):
        if this.creator is not None:
            return this.creator.nickname

        return None

    @property
    def roster (this):
        return this.members.all ()

    @property
    @extend_schema_field (serializers.CharField ())
    def chat_channel_id (this):
        return Sendbird.build_channel_url ('team', this.shareable_uid)
