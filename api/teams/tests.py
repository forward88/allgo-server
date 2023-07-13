import random
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from schoolyard.tests import reverse_with_query
from api.users.models import APIUser, APIUserState
from api.teams.models import Team, TeamInvitationStatus
from api.rest_auth.tests import active_api_user_test, set_active_api_credentials


__all__ = ['TeamTests']

class TeamTests (APITestCase):
    fixtures = ['required/sms-notifications', 'testing/users-valid']

    user_queryset = APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False)

    def create_team (this, *, creator=None):
        if creator is None:
            creator = this.api_user

        url = reverse ('api.teams:create')

        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)

        return response.data ['team_uid']

    @active_api_user_test
    def test_create_first_team (this):
        team_uid = this.create_team ()

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['team_uid'], team_uid)

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_uid})
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['creator'], this.api_user.user_profile.nickname)

    @active_api_user_test
    def test_create_second_team (this):
        team_a_uid = this.create_team ()
        team_b_uid = this.create_team ()

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_a_uid})
        response = this.client.get (url)
        this.assertEqual (response.data ['creator'], this.api_user.user_profile.nickname)
        this.assertNotIn (this.api_user.user_profile.nickname, [ member ['nickname'] for member in response.data ['roster'] ])

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_b_uid})
        response = this.client.get (url)
        this.assertEqual (response.data ['creator'], this.api_user.user_profile.nickname)
        this.assertIn (this.api_user.user_profile.nickname, [ member ['nickname'] for member in response.data ['roster'] ])

        team_a = Team.objects.get (shareable_uid=team_a_uid)
        team_b = Team.objects.get (shareable_uid=team_b_uid)

        this.assertEqual (team_a.user_created, True)
        this.assertEqual (team_b.user_created, True)

    def test_invite_users (this):
        inviters = random.sample (list (this.user_queryset), 5)

        invitee_expected_invitation_lists = {}
        inviter_expected_invitation_lists = {}
        for inviter in inviters:
            set_active_api_credentials (this, inviter)

            team_uid = this.create_team (creator=inviter)

            invitees = random.sample (list (this.user_queryset.exclude (pk=inviter.pk)), 3)
            invitee_list = ','.join ([ str (invitee.phone_number) for invitee in invitees ])

            url = reverse_with_query ('api.teams:invite', query_params={'team_uid': team_uid, 'invitee_phone_numbers': invitee_list})
            response = this.client.get (url)
            this.assertEqual (response.status_code, status.HTTP_200_OK)

            inviter_expected_invitation_lists [inviter] = []
            for invitee in invitees:
                if invitee not in invitee_expected_invitation_lists:
                    invitee_expected_invitation_lists [invitee] = []

                invitation_data = (inviter.user_profile.nickname, invitee.user_profile.nickname, team_uid)

                invitee_expected_invitation_lists [invitee].append (invitation_data)
                inviter_expected_invitation_lists [inviter].append (invitation_data)

        for (invitee, expected_invitations) in invitee_expected_invitation_lists.items ():
            set_active_api_credentials (this, invitee)

            url = reverse ('api.teams:list-invites')
            response = this.client.get (url)

            invitations = [ (invitation ['inviter'] ['nickname'], invitation ['invitee'] ['nickname'], invitation ['team'] ['team_uid']) for invitation in response.data ]

            if invitee in inviter_expected_invitation_lists.keys ():
                expected_invitations.extend (inviter_expected_invitation_lists [invitee])

            this.assertListEqual (invitations, expected_invitations)

    def test_accept_invite (this):
        (inviter, invitee) = random.sample (list (this.user_queryset), 2)

        set_active_api_credentials (this, inviter)

        team_uid = this.create_team (creator=inviter)

        url = reverse_with_query ('api.teams:invite', query_params={'team_uid': team_uid, 'invitee_phone_numbers': str (invitee.phone_number)})
        response = this.client.get (url)

        set_active_api_credentials (this, invitee)

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['team_uid'], None)

        url = reverse_with_query ('api.teams:accept-invite', query_params={'team_uid': team_uid})
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertTrue (response.data ['success'])

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['team_uid'], team_uid)

        url = reverse ('api.teams:list-invites')
        response = this.client.get (url)
        this.assertEqual (len (response.data), 1)
        this.assertEqual (response.data [0] ['status'], TeamInvitationStatus.ACCEPTED.name)

    def test_accept_second_invite (this):
        (inviter, invitee) = random.sample (list (this.user_queryset), 2)

        set_active_api_credentials (this, inviter)

        team_a_uid = this.create_team (creator=inviter)
        team_b_uid = this.create_team (creator=inviter)

        url = reverse_with_query ('api.teams:invite', query_params={'team_uid': team_a_uid, 'invitee_phone_numbers': str (invitee.phone_number)})
        response = this.client.get (url)

        set_active_api_credentials (this, invitee)

        url = reverse_with_query ('api.teams:accept-invite', query_params={'team_uid': team_a_uid})
        response = this.client.get (url)

        url = reverse_with_query ('api.teams:accept-invite', query_params={'team_uid': team_b_uid})
        response = this.client.get (url)

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.data ['team_uid'], team_b_uid)

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_a_uid})
        response = this.client.get (url)
        this.assertNotIn (invitee.user_profile.nickname, [ member ['nickname'] for member in response.data ['roster'] ])

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_b_uid})
        response = this.client.get (url)
        this.assertIn (invitee.user_profile.nickname, [ member ['nickname'] for member in response.data ['roster'] ])

    def test_decline_invite (this):
        (inviter, invitee) = random.sample (list (this.user_queryset), 2)

        set_active_api_credentials (this, inviter)

        team_uid = this.create_team (creator=inviter)

        url = reverse_with_query ('api.teams:invite', query_params={'team_uid': team_uid, 'invitee_phone_numbers': str (invitee.phone_number)})
        response = this.client.get (url)

        set_active_api_credentials (this, invitee)

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['team_uid'], None)

        url = reverse_with_query ('api.teams:decline-invite', query_params={'team_uid': team_uid})
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertTrue (response.data ['success'])

        url = reverse ('api.users:user-detail')
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['team_uid'], None)

        url = reverse ('api.teams:list-invites')
        response = this.client.get (url)
        this.assertEqual (len (response.data), 0)

    @active_api_user_test
    def test_team_member_list (this):
        inviter = this.api_user

        team_uid = this.create_team ()

        invitees = random.sample (list (this.user_queryset.exclude (pk=inviter.pk)), 3)
        invitee_list = ','.join ([ str (invitee.phone_number) for invitee in invitees ])

        url = reverse_with_query ('api.teams:invite', query_params={'team_uid': team_uid, 'invitee_phone_numbers': invitee_list})
        response = this.client.get (url)

        for invitee in invitees:
            set_active_api_credentials (this, invitee)

            url = reverse_with_query ('api.teams:accept-invite', query_params={'team_uid': team_uid})
            response = this.client.get (url)

        url = reverse_with_query ('api.teams:detail', query_params={'team_uid': team_uid})
        response = this.client.get (url)
        members = [ member ['nickname'] for member in response.data ['roster'] ]
        expected_members = [ invitee.user_profile.nickname for invitee in invitees ] + [inviter.user_profile.nickname]

        this.assertListEqual (sorted (members), sorted (expected_members))
