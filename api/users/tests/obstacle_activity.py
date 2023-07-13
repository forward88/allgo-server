import random
from datetime import timedelta
from decimal import Decimal

import freezegun

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework import status
from rest_framework.test import APITestCase

from schoolyard import settings
from schoolyard.tests import reverse_with_query, DurationTestCase
from api.users.views import AddObstacleActivityErrorMessage
from api.users.models import UserObstacle
from api.rest_auth.tests import active_api_user_test
from api.challenges.models import Challenge, Obstacle
from api.events.models import calculate_registered_amount, ObstacleActivityEvent

__all__ = ['ObstacleActivityTests', 'AddObstacleActivityTests']

error_detail_key = settings.REST_FRAMEWORK ['NON_FIELD_ERRORS_KEY']

class ObstacleActivityTests (DurationTestCase):
    fixtures = [
        'required/challenge_categories',
        'required/challenge_color_profiles',
        'testing/users-valid',
        'testing/obstacle-tasks',
        'testing/challenges-obstacles' ]

    @active_api_user_test
    def test_current_obstacles (this):
        offsets = {}
        durations = {}

        for d in [1, 7, 28]:
            for challenge in random.sample (list (Challenge.objects.filter (duration=timedelta (days=d))), 3):
                url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge.pk, 'action': 'JOIN'})

                offset = timedelta (seconds=random.randrange ((d + 1) * settings.DAY_S))

                mock_date = freezegun.freeze_time (timezone.now () - offset)
                mock_date.start ()
                response = this.client.get (url)
                mock_date.stop ()

                this.assertEqual (response.status_code, status.HTTP_200_OK)

                offsets [challenge.name] = offset
                durations [challenge.name] = challenge.duration

        url = reverse ('api.users:user-obstacle-list')
        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)

        for (name, d) in [('DAILY', 1), ('WEEKLY', 7), ('MONTHLY', 28)]:
            obstacle_duration = timedelta (days=d)
            for obstacle_data in response.data [name]:
                challenge_elapsed_duration = offsets [obstacle_data ['challenge'] ['name']]
                challenge_duration = durations [obstacle_data ['challenge'] ['name']]
                obstacle_elapsed_duration = challenge_elapsed_duration % obstacle_duration

                expected_rank = (challenge_elapsed_duration % challenge_duration) // obstacle_duration + 1
                expected_remaining_duration = obstacle_duration - obstacle_elapsed_duration

                this.assertEqual (expected_rank, obstacle_data ['sequence_rank'])
                this.assertDurationsEqual (timedelta (seconds=obstacle_data ['remaining_seconds']), expected_remaining_duration)

class AddObstacleActivityTests (APITestCase):
    fixtures = [
        'required/challenge_categories',
        'required/challenge_color_profiles',
        'testing/users-valid',
        'testing/obstacle-tasks',
        'testing/challenges-obstacles',
        'testing/users-activity' ]

    @active_api_user_test
    def test_invalid_obstacle (this):
        obstacle_query = UserObstacle.objects.all () \
            .values_list ('obstacle', flat=True) \
            .annotate (user_list=ArrayAgg ('user_challenge__user')) \
            .filter (~models.Q (user_list__contains=[this.api_user.user_profile.pk]))

        for obstacle_id in obstacle_query:
            query_params = {'obstacle_id': obstacle_id, 'sequence_rank': 1, 'amount': 1}
            url = reverse_with_query ('api.users:add-obstacle-activity', query_params=query_params)
            response = this.client.get (url)
            this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
            this.assertEqual (response.data [0], AddObstacleActivityErrorMessage.INVALID_OBSTACLE.value)

    @active_api_user_test
    def test_user_mismatch (this):
        user_obstacle = random.choice (UserObstacle.objects.exclude (user_challenge__user=this.api_user.user_profile))

        query_params = {'obstacle_id': user_obstacle.obstacle.pk, 'sequence_rank': user_obstacle.sequence_rank, 'amount': 1}
        url = reverse_with_query ('api.users:add-obstacle-activity', query_params=query_params)

        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
        this.assertEqual (response.data [0], AddObstacleActivityErrorMessage.INVALID_OBSTACLE.value)

    @active_api_user_test
    def test_misapplied_float_amount (this):
        user_obstacle = random.choice (UserObstacle.objects.filter (user_challenge__user=this.api_user.user_profile, obstacle__task__discrete=True))

        query_params = {'obstacle_id': user_obstacle.obstacle.pk, 'sequence_rank': user_obstacle.sequence_rank, 'amount': 0.1}
        url = reverse_with_query ('api.users:add-obstacle-activity', query_params=query_params)

        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
        this.assertEqual (response.data [0], AddObstacleActivityErrorMessage.MISAPPLIED_FLOAT_AMOUNT.value)

    @active_api_user_test
    def test_valid_add (this):
        expected_amounts = {}
        for user_obstacle in this.api_user.user_profile.current_obstacles:
            if user_obstacle.obstacle.task.discrete:
                extreme_amount = 2 * user_obstacle.obstacle.threshold
                amount = Decimal (str (random.randint (-extreme_amount, extreme_amount)))
            else:
                extreme_amount = 2.0 * float (user_obstacle.obstacle.threshold)
                amount = Decimal (str (round (random.uniform (-extreme_amount, extreme_amount), 1)))

            expected_amount_registered = calculate_registered_amount (amount, user_obstacle.amount_completed, user_obstacle.obstacle.threshold)
            expected_amount_key = f"{user_obstacle.challenge.pk}-{user_obstacle.obstacle.pk}-{user_obstacle.sequence_rank}"
            expected_amounts [expected_amount_key] = user_obstacle.amount_completed + expected_amount_registered

            query_params = {'obstacle_id': user_obstacle.obstacle.pk, 'sequence_rank': user_obstacle.sequence_rank, 'amount': amount}
            url = reverse_with_query ('api.users:add-obstacle-activity', query_params=query_params)

            response = this.client.get (url)
            this.assertEqual (response.status_code, status.HTTP_200_OK)
            this.assertEqual (response.data ['amount_registered'], expected_amount_registered)

        url = reverse ('api.users:user-obstacle-list')
        response = this.client.get (url)

        for obstacle_data_set in response.data.values ():
            for obstacle_data in obstacle_data_set:
                expected_amount_key = f"{obstacle_data ['challenge'] ['challenge_id']}-{obstacle_data ['obstacle'] ['obstacle_id']}-{obstacle_data ['sequence_rank']}"
                this.assertEqual (obstacle_data ['amount_completed'], expected_amounts [expected_amount_key])

class UserStreakTests (APITestCase):
    fixtures = [
        'required/challenge_categories',
        'required/challenge_color_profiles',
        'testing/users-valid',
        'testing/obstacle-tasks',
        'testing/challenges-obstacles' ]

    @active_api_user_test
    def test_streak(self):
        challenge_pk = random.choice (list (set (Obstacle.objects.filter (interval__in=['W', 'M'], threshold__gt=3).values_list ('challenge_id', flat=True))))

        url = reverse_with_query ('api.users:do-challenge-action', query_params={'challenge_id': challenge_pk, 'action': 'JOIN'})
        self.client.get (url)

        self.assertEqual (self.api_user.user_profile.streak, 0)

        obstacle = Challenge.objects.get (pk=challenge_pk).obstacles.first ()

        now = timezone.now()
        with freezegun.freeze_time(now + timedelta(days=1)):
            self.api_user.user_profile.do_obstacle_activity(obstacle, 1, 1)
            self.assertEqual(self.api_user.user_profile.streak, 1)

        with freezegun.freeze_time(now + timedelta(days=2)):
            self.api_user.user_profile.do_obstacle_activity(obstacle, 1, 1)
            self.assertEqual(self.api_user.user_profile.streak, 2)

        with freezegun.freeze_time(now + timedelta(days=4)):
            self.api_user.user_profile.do_obstacle_activity(obstacle, 1, 1)
            self.assertEqual(self.api_user.user_profile.streak, 1)
