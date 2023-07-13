from rest_framework.response import Response as APIResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.rest_auth.views import ActiveAPIUserView
from api.teams.models import Team
from api.teams.serializers import TeamSerializer, LeaveTeamSerializer, InviteTeamSerializer, TeamInvitationSerializer, InvitationAcceptSerializer, InvitationDeclineSerializer

__all__ = ['CreateTeamView', 'LeaveTeamView', 'InviteTeamView', 'InvitationListView', 'InvitationAcceptView', 'InvitationDeclineView', 'TeamDetailView']

class CreateTeamView (ActiveAPIUserView):
    @extend_schema (responses=TeamSerializer)
    def get (this, request):
        team = request.user.user_profile.create_team ()
        serializer = TeamSerializer (team)

        return APIResponse (serializer.data)

class LeaveTeamView (ActiveAPIUserView):
    @extend_schema (responses=LeaveTeamSerializer)
    def get (this, request):
        request.user.user_profile.leave_team ()

        serializer = LeaveTeamSerializer (data={'success': True})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class InviteTeamView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='team_uid',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True),
            OpenApiParameter (
                name='invitee_phone_numbers',
                type={'type': 'array', 'items': {'type': 'string'}},
                location=OpenApiParameter.QUERY,
                required=True,
                description='A comma-separated list of phone numbers.',
                style='simple') ],
        responses=InviteTeamSerializer)
    def get (this, request):
        user = request.user.user_profile
        team_uid = request.GET.get ('team_uid')
        invitee_phone_numbers = request.GET.get ('invitee_phone_numbers').split (',')

        for phone_number in invitee_phone_numbers:
            user.invite_team_member (team_uid, phone_number)

        serializer = InviteTeamSerializer (data={'success': True})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class InvitationListView (ActiveAPIUserView):
    @extend_schema (responses=TeamInvitationSerializer (many=True))
    def get (this, request):
        serializer = TeamInvitationSerializer (request.user.user_profile.all_invitations, many=True)

        return APIResponse (serializer.data)

class InvitationAcceptView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='team_uid',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=InvitationAcceptSerializer)
    def get (this, request):
        user = request.user.user_profile
        team_uid = request.GET.get ('team_uid')

        user.accept_team_invitation (team_uid)

        serializer = InvitationAcceptSerializer (data={'team_uid': team_uid})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class InvitationDeclineView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='team_uid',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True) ],
        responses=InvitationDeclineSerializer)
    def get (this, request):
        user = request.user.user_profile
        team_uid = request.GET.get ('team_uid')

        user.decline_team_invitation (team_uid)

        serializer = InvitationDeclineSerializer (data={'team_uid': team_uid})
        serializer.is_valid (raise_exception=True)

        return APIResponse (serializer.validated_data)

class TeamDetailView (ActiveAPIUserView):
    @extend_schema (
        parameters=[
            OpenApiParameter (
                name='team_uid',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True) ],
            responses=TeamSerializer)
    def get (this, request):
        team_uid = request.GET.get ('team_uid')

        serializer = TeamSerializer (Team.objects.get (shareable_uid=team_uid))

        return APIResponse (serializer.data)
