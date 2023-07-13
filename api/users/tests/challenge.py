import random
from datetime import date, timedelta

import freezegun

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework import status

from schoolyard.tests import reverse_with_query, DurationTestCase
from schoolyard.settings import DAY_S
from api.rest_auth.tests import active_api_user_test
from api.users.models import UserChallengeState, UserChallenge
from api.challenges.models import Challenge
from api.users.views import UserChallengeViewErrorMessage

__all__ = ['UserChallengeTests']

ERROR_DETAIL_KEY = settings.REST_FRAMEWORK ['NON_FIELD_ERRORS_KEY']

class UserChallengeTests (DurationTestCase):
    fixtures = [
        'required/challenge_categories',
        'required/challenge_color_profiles',
        'testing/users-valid',
        'testing/obstacle-tasks',
        'testing/challenges-obstacles' ]

    user_challenges_url = reverse ('api.users:user-challenge-list')

    def validate_first_joins (this, challenges, offsets):
        for (challenge, offset) in zip (challenges, offsets + [0]):
            url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'JOIN'})

            mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=offset))
            mock_date.start ()
            response = this.client.get (url)
            mock_date.stop ()

            this.assertEqual (response.status_code, status.HTTP_200_OK)
            this.assertEqual (response.data ['iteration'], 1)

        response = this.client.get (this.user_challenges_url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)

        expected_remaining_duration = [challenges [1].duration - timedelta (seconds=offsets [1]), challenges [2].duration]

        for (cp, expected_remaining) in zip (sorted (response.data ['open_challenges'], key=lambda cp : cp ['remaining_seconds']), sorted (expected_remaining_duration)):
            this.assertEqual (cp ['state'], 'ACTIVE')
            this.assertDurationsEqual (timedelta (seconds=cp ['remaining_seconds']), expected_remaining)

        this.assertEqual (response.data ['closed_challenges'] [0] ['state'], 'EXPIRED')
        this.assertDurationsEqual (timedelta (seconds=response.data ['closed_challenges'] [0] ['remaining_seconds']), timedelta (0))

    @active_api_user_test
    def test_join_challenge_one_day_first_iteration (this):
        challenges = random.sample (list (Challenge.objects.filter (duration=timedelta (days=1))), 3)

        expired_offset = random.randrange (2 * DAY_S, 10 * DAY_S)
        unexpired_offset = random.randrange (0.5 * DAY_S, DAY_S)

        this.validate_first_joins (challenges, [expired_offset, unexpired_offset])

    @active_api_user_test
    def test_join_challenge_multi_day_first_iteration (this):
        challenges = random.sample (list (Challenge.objects.filter (duration__gt=timedelta (days=1))), 3)

        expired_offset = random.randrange ((2 + challenges [0].duration_days) * DAY_S, (10 + challenges [0].duration_days) * DAY_S)
        unexpired_offset = random.randrange (DAY_S, (challenges [1].duration_days - 1) * DAY_S)

        this.validate_first_joins (challenges, [expired_offset, unexpired_offset])

    @active_api_user_test
    def test_join_challenge_second_iteration (this):
        offset_base = random.randrange (5 * DAY_S, 10 * DAY_S)

        challenge_sets = [ random.sample (list (Challenge.objects.filter (duration=timedelta (days=d))), 3) for d in [1, 7, 28] ]
        for challenge_set in challenge_sets:
            for challenge in challenge_set:
                url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'JOIN'})

                offset_start = timedelta (seconds=offset_base) + challenge.duration
                offset_unexpired = offset_start - timedelta (seconds=random.randrange (challenge.duration.total_seconds ()))

                # first iteration
                mock_date = freezegun.freeze_time (timezone.now () - offset_start)
                mock_date.start ()
                this.client.get (url)
                mock_date.stop ()

                # second iteration attempt, pre-expiration
                mock_date = freezegun.freeze_time (timezone.now () - offset_unexpired)
                mock_date.start ()
                response = this.client.get (url)
                mock_date.stop ()

                expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action='JOIN', previous_action='JOIN')
                this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
                this.assertEqual (response.data [0], expected_error_msg)

                # second iteration attempt, post-expiration
                response = this.client.get (url)
                this.assertEqual (response.status_code, status.HTTP_200_OK)

        response = this.client.get (this.user_challenges_url)

        this.assertEqual (len (response.data ['open_challenges']), 9)
        for cp in response.data ['open_challenges']:
            this.assertEqual (cp ['state'], 'ACTIVE')
            this.assertEqual (cp ['iteration'], 2)

        this.assertEqual (len (response.data ['closed_challenges']), 9)
        for cp in response.data ['closed_challenges']:
            this.assertEqual (cp ['state'], 'EXPIRED')
            this.assertEqual (cp ['iteration'], 1)

    def validate_invalid_action (this, url, expected_error_msg):
        response = this.client.get (url)
        this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
        this.assertEqual (response.data [0], expected_error_msg)

    @active_api_user_test
    def test_invalid_action (this):
        invalid_transition_error_msg = lambda action, state : ChallengeParticipationErrorMessage.INVALID_ACTION.value.format (action=action, state=state.label)

        challenge_left, challenge_expired = random.sample (list (Challenge.objects.all ()), 2)

        action_url = lambda action : reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge_left.pk, 'action': action})

        # test invalid actions (no participation)
        for action in ['PAUSE', 'UNPAUSE', 'LEAVE']:
            expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action=action, previous_action=None)
            this.validate_invalid_action (action_url (action), expected_error_msg)

        # join challenge
        this.client.get (action_url ('JOIN'))

        # test invalid join (existing participation)
        expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action='JOIN', previous_action='JOIN')
        this.validate_invalid_action (action_url ('JOIN'), expected_error_msg)

        # test invalid unpause (active participation)
        expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action='UNPAUSE', previous_action='JOIN')
        this.validate_invalid_action (action_url ('UNPAUSE'), expected_error_msg)

        # pause challenge
        this.client.get (action_url ('PAUSE'))

        # test invalid pause (already paused)
        expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action='PAUSE', previous_action='PAUSE')
        this.validate_invalid_action (action_url ('PAUSE'), expected_error_msg)

        # unpause challenge
        this.client.get (action_url ('UNPAUSE'))

        # test invalid unpause (already unpaused)
        expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action='UNPAUSE', previous_action='UNPAUSE')
        this.validate_invalid_action (action_url ('UNPAUSE'), expected_error_msg)

        # leave challenge
        this.client.get (action_url ('LEAVE'))

        # test invalid actions (left challenge)
        for action in ['PAUSE', 'UNPAUSE', 'LEAVE']:
            expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action=action, previous_action=None)
            this.validate_invalid_action (action_url (action), expected_error_msg)

        # test invalid action (expired challenge)
        action_url = lambda action : reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge_expired.pk, 'action': action})

        offset = timedelta (days=challenge_expired.duration_days + 2)
        mock_date = freezegun.freeze_time (date.today () - offset)
        mock_date.start ()
        this.client.get (action_url ('JOIN'))
        mock_date.stop ()

        for action in ['PAUSE', 'UNPAUSE', 'LEAVE']:
            expected_error_msg = UserChallengeViewErrorMessage.INVALID_CHALLENGE_ACTION.value.format (action=action, previous_action=None)
            this.validate_invalid_action (action_url (action), expected_error_msg)

    @active_api_user_test
    def test_pause_challenge (this):
        offset_base = timedelta (seconds=random.randrange (2 * DAY_S, 8 * DAY_S))

        challenge_sets = [random.sample (list (Challenge.objects.filter (duration=timedelta (days=d))), 3) for d in [1, 7, 28]]
        for (challenge_0, challenge_1, challenge_2) in challenge_sets:
            offset_join = offset_base + challenge_0.duration
            offset_pause = offset_join - timedelta (seconds=random.randrange (challenge_0.duration.total_seconds ()))

            offset_expired = challenge_0.duration + timedelta (days=100)

            (join_0_url, join_1_url, join_2_url) = [
                reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'JOIN'})
                for challenge in (challenge_0, challenge_1, challenge_2) ]

            # prime challenge_0 with expired iteration
            t = timezone.now () - offset_expired
            mock_date = freezegun.freeze_time (t)
            mock_date.start ()
            this.client.get (join_0_url)
            mock_date.stop ()

            # join challenges
            t = timezone.now () - offset_join
            mock_date = freezegun.freeze_time (t)
            mock_date.start ()
            this.client.get (join_0_url)
            this.client.get (join_1_url)
            this.client.get (join_2_url)
            mock_date.stop ()

            # pause challenges
            (pause_0_url, pause_1_url) = [
                reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'PAUSE'})
                for challenge in (challenge_0, challenge_1) ]

            t = timezone.now () - offset_pause
            mock_date = freezegun.freeze_time (t)
            mock_date.start ()
            this.client.get (pause_0_url)
            this.client.get (pause_1_url)

            # check remaining_days, state, and iteration immediately after pause
            (response_0, response_1, response_2) = [
                this.client.get (reverse_with_query ('api.users:user-challenge-detail', query_params={'challenge_id': challenge.pk}))
                for challenge in (challenge_0, challenge_1, challenge_2) ]
            mock_date.stop ()

            for response in [response_0, response_1, response_2]:
                this.assertDurationsEqual (timedelta (seconds=response.data ['remaining_seconds']), offset_pause - offset_base)

            this.assertEqual (response_0.data ['iteration'], 2)
            this.assertEqual (response_0.data ['state'], UserChallengeState.PAUSED.name)

            this.assertEqual (response_1.data ['iteration'], 1)
            this.assertEqual (response_1.data ['state'], UserChallengeState.PAUSED.name)

            this.assertEqual (response_2.data ['iteration'], 1)
            this.assertEqual (response_2.data ['state'], UserChallengeState.ACTIVE.name)

            # check remaining_days, state, and iteration today
            response = this.client.get (this.user_challenges_url)

            for cp in response.data ['open_challenges']:
                if cp ['challenge'] ['name'] == challenge_0.name:
                    this.assertEqual (cp ['iteration'], 2)
                    this.assertEqual (cp ['state'], UserChallengeState.PAUSED.name)
                    this.assertDurationsEqual (timedelta (seconds=cp ['remaining_seconds']), offset_pause - offset_base)
                elif cp ['challenge'] ['name'] == challenge_1.name:
                    this.assertEqual (cp ['iteration'], 1)
                    this.assertEqual (cp ['state'], UserChallengeState.PAUSED.name)
                    this.assertDurationsEqual (timedelta (seconds=cp ['remaining_seconds']), offset_pause - offset_base)
                elif cp ['challenge'] ['name'] == challenge_2.name:
                    this.assertEqual (cp ['iteration'], 1)
                    this.assertEqual (cp ['state'], UserChallengeState.EXPIRED.name)
                    this.assertDurationsEqual (timedelta (seconds=cp ['remaining_seconds']), timedelta (0))
                else:
                    pass

    def validate_pause_unpause_cycle_probe (this, challenge_cycled, challenge_control, offset_probe, expected_remaining_cycled, expected_remaining_control):
        mock_date = freezegun.freeze_time (timezone.now () - offset_probe)
        mock_date.start ()

        response_cycled = this.client.get (reverse_with_query ('api.users:user-challenge-detail', query_params={'challenge_id': challenge_cycled.pk}))
        response_control = this.client.get (reverse_with_query ('api.users:user-challenge-detail', query_params={'challenge_id': challenge_control.pk}))

        this.assertDurationsEqual (timedelta (seconds=response_cycled.data ['remaining_seconds']), expected_remaining_cycled)
        this.assertDurationsEqual (timedelta (seconds=response_control.data ['remaining_seconds']), expected_remaining_control)

        mock_date.stop ()

    @active_api_user_test
    def test_pause_unpause_cycle (this):
        (challenge_cycled, challenge_control) = random.sample (list (Challenge.objects.filter (duration=timedelta (days=28))), 2)

        (cycled_join_url, control_join_url) = [ reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': c.pk, 'action': 'JOIN'}) for c in (challenge_cycled, challenge_control) ]
        pause_url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge_cycled.pk, 'action': 'PAUSE'})
        unpause_url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge_cycled.pk, 'action': 'UNPAUSE'})

        offset_base = timedelta (seconds=random.randrange (99 * DAY_S, 101 * DAY_S))
        offset_start = offset_base + challenge_control.duration
        offset_pause_0 = offset_start - timedelta (seconds=random.randrange (1 * DAY_S, 7 * DAY_S))
        offset_unpause_0 = offset_pause_0 - timedelta (seconds=random.randrange (1 * DAY_S, 7 * DAY_S))
        offset_probe_00 = timedelta (seconds=random.randrange (offset_unpause_0.total_seconds (), offset_pause_0.total_seconds ()))
        offset_pause_1 = offset_unpause_0 - timedelta (seconds=random.randrange (1 * DAY_S, 7 * DAY_S))
        offset_probe_01 = timedelta (seconds=random.randrange (offset_pause_1.total_seconds (), offset_unpause_0.total_seconds ()))
        offset_unpause_1 = offset_pause_1 - timedelta (seconds=random.randrange (1 * DAY_S, 7 * DAY_S))
        offset_probe_11 = timedelta (seconds=random.randrange (offset_unpause_1.total_seconds (), offset_pause_1.total_seconds ()))

        # start cycle
        mock_date = freezegun.freeze_time (timezone.now () - offset_start)
        mock_date.start ()
        this.client.get (cycled_join_url)
        this.client.get (control_join_url)
        mock_date.stop ()

        # pause_0
        mock_date = freezegun.freeze_time (timezone.now () - offset_pause_0)
        mock_date.start ()
        this.client.get (pause_url)
        mock_date.stop ()

        # probe_00
        expected_remaining_cycled = challenge_control.duration - (offset_start - offset_pause_0)
        expected_remaining_control = challenge_control.duration - (offset_start - offset_probe_00)
        this.validate_pause_unpause_cycle_probe (challenge_cycled, challenge_control, offset_probe_00, expected_remaining_cycled, expected_remaining_control)

        # unpause_0
        mock_date = freezegun.freeze_time (timezone.now () - offset_unpause_0)
        mock_date.start ()
        this.client.get (unpause_url)
        mock_date.stop ()

        # probe_01
        expected_remaining_cycled -= offset_unpause_0 - offset_probe_01
        expected_remaining_control = challenge_control.duration - (offset_start - offset_probe_01)
        this.validate_pause_unpause_cycle_probe (challenge_cycled, challenge_control, offset_probe_01, expected_remaining_cycled, expected_remaining_control)

        # pause_1
        mock_date = freezegun.freeze_time (timezone.now () - offset_pause_1)
        mock_date.start ()
        this.client.get (pause_url)
        mock_date.stop ()

        # probe_11
        expected_remaining_cycled -= offset_probe_01 - offset_pause_1
        expected_remaining_control = challenge_control.duration - (offset_start - offset_probe_11)
        this.validate_pause_unpause_cycle_probe (challenge_cycled, challenge_control, offset_probe_11, expected_remaining_cycled, expected_remaining_control)

        # unpause_1
        mock_date = freezegun.freeze_time (timezone.now () - offset_unpause_1)
        mock_date.start ()
        this.client.get (unpause_url)
        mock_date.stop ()

        # probe_12
        offset_probe_12 = offset_unpause_1 - timedelta (seconds=random.randrange (expected_remaining_control.total_seconds () + 1 * DAY_S, expected_remaining_cycled.total_seconds ()))
        expected_remaining_cycled -= offset_unpause_1 - offset_probe_12
        expected_remaining_control = timedelta (0)

        mock_date = freezegun.freeze_time (timezone.now () - offset_probe_12)
        mock_date.start ()
        response = this.client.get (this.user_challenges_url)

        response_cycled = this.client.get (reverse_with_query ('api.users:user-challenge-detail', query_params={'challenge_id': challenge_cycled.pk}))
        response_control = this.client.get (reverse_with_query ('api.users:user-challenge-detail', query_params={'challenge_id': challenge_control.pk}))

        this.assertDurationsEqual (timedelta (seconds=response_cycled.data ['remaining_seconds']), expected_remaining_cycled)
        this.assertDurationsEqual (timedelta (seconds=response_control.data ['remaining_seconds']), expected_remaining_control)

        mock_date.stop ()

    @active_api_user_test
    def test_leave_challenge (this):
        now = timezone.now ()

        (challenge_1, challenge_7, challenge_28) = [ random.choice (Challenge.objects.filter (duration=timedelta (days=d))) for d in [1, 7, 28] ]

        for challenge in [challenge_1, challenge_7, challenge_28]:
            offset_base = timedelta (seconds=random.randrange (2 * DAY_S, 8 * DAY_S))
            offset_join = offset_base + challenge.duration
            offset_leave = offset_join - timedelta (seconds=random.randrange (challenge.duration.total_seconds ()))

            join_url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'JOIN'})
            leave_url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'LEAVE'})

            # join challenge
            mock_date = freezegun.freeze_time (now - offset_join)
            mock_date.start ()
            this.client.get (join_url)
            mock_date.stop ()

            # leave challenge
            mock_date = freezegun.freeze_time (now - offset_leave)
            mock_date.start ()
            this.client.get (leave_url)
            mock_date.stop ()

            cp_model = UserChallenge.objects.get (challenge=challenge)
            this.assertEqual (cp_model.elapsed_duration, offset_join - offset_leave)

        response = this.client.get (this.user_challenges_url)

        this.assertEqual (len (response.data ['open_challenges']), 0)
        this.assertEqual (len (response.data ['closed_challenges']), 3)

        for cp in response.data ['closed_challenges']:
            this.assertDurationsEqual (timedelta (seconds=cp ['remaining_seconds']), timedelta (0))
            this.assertEqual (cp ['state'], UserChallengeState.LEFT.name)
