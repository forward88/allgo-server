from django.db import models

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

__all__ = ['TeamInvitationStatus', 'TeamInvitation']

class TeamInvitationStatus (models.TextChoices):
    PENDING = ('P', 'Pending')
    ACCEPTED = ('A', 'Accepted')
    DECLINED = ('D', 'Declined')

class TeamInvitation (models.Model):
    inviter = models.ForeignKey ('users.APIUser', on_delete=models.SET_NULL, related_name='sent_invitations', null=True)
    invitee = models.ForeignKey ('users.APIUser', on_delete=models.CASCADE, related_name='received_invitations')
    team = models.ForeignKey ('Team', on_delete=models.CASCADE, related_name='invitations')
    status = models.CharField (max_length=1, choices=TeamInvitationStatus.choices, default=TeamInvitationStatus.PENDING)
    ctime = models.DateTimeField (auto_now_add=True, verbose_name="Created At")

    class Meta:
        constraints = [ models.UniqueConstraint (name='unique_invitee_team', fields=['invitee', 'team'], condition=models.Q (status=TeamInvitationStatus.PENDING.value)) ]

    @property
    @extend_schema_field (serializers.CharField ())
    def inviter_nickname (this):
        return this.inviter.user_profile.nickname

    @property
    @extend_schema_field (serializers.CharField ())
    def team_uid (this):
        return this.team.shareable_uid

    @property
    def status_name (this):
        return TeamInvitationStatus (this.status).name
