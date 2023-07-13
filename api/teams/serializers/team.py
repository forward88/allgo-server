from rest_framework import serializers

from api.teams.models import Team, TeamInvitation
from api.users.serializers import UserProfileDetailSerializer

__all__ = ['TeamSerializer', 'TeamInvitationSerializer', 'LeaveTeamSerializer', 'InviteTeamSerializer', 'InvitationAcceptSerializer', 'InvitationDeclineSerializer']

class TeamSerializer (serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['creator', 'team_uid', 'roster', 'xp_earned', 'chat_channel_id']

    creator = serializers.CharField (source='creator_nickname')
    team_uid = serializers.CharField (source='shareable_uid')
    roster = UserProfileDetailSerializer (many=True)

class TeamInvitationSerializer (serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = ['inviter', 'invitee', 'team', 'status']

    team = TeamSerializer()
    status = serializers.CharField(source='status_name')
    inviter = UserProfileDetailSerializer (source='inviter.user_profile')
    invitee = UserProfileDetailSerializer (source='invitee.user_profile')

class LeaveTeamSerializer (serializers.Serializer):
    success = serializers.BooleanField ()

    def validate (this, data):
        return data

class InviteTeamSerializer (serializers.Serializer):
    success = serializers.BooleanField ()

    def validate (this, data):
        return data

class InvitationAcceptSerializer (serializers.Serializer):
    team_uid = serializers.CharField (max_length=Team._meta.get_field ('shareable_uid').max_length, write_only=True)
    success = serializers.BooleanField (read_only=True)

    def validate (this, data):
        return {'success': True}

class InvitationDeclineSerializer (InvitationAcceptSerializer):
    pass
