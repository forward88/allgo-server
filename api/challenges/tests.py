import random

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from schoolyard.tests import reverse_with_query
from ..rest_auth.tests import anonymous_api_user_test
from .models import Challenge, ChallengeCategory, Obstacle

class ChallengeTests (APITestCase):
    fixtures = [
        'required/challenge_categories',
        'required/challenge_color_profiles',
        'testing/users-valid',
        'testing/obstacle-tasks',
        'testing/challenges-obstacles' ]

    @anonymous_api_user_test
    def test_categories (this):
        url = reverse ('api.challenges:challenge-category-list')
        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (len (response.data), 9)

    @anonymous_api_user_test
    def test_challenge_list_api_status (this):
        url = reverse ('api.challenges:challenge-list')
        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)

    @anonymous_api_user_test
    def test_challenge_list_api_response (this):
        url = reverse ('api.challenges:challenge-list')
        response = this.client.get (url)

        this.assertEqual (len (response.data), 18)

    @anonymous_api_user_test
    def test_challenge_list_categories_filter_api_response (this):
        this.challenge_categories = {}
        for category in ChallengeCategory.objects.all ():
            this.challenge_categories [category.pk] = category

        for i in range (3):
            for sample_set in [random.sample ([str (pk) for pk in range (1, 10)], k) for k in range (1, 6)]:
                expected_count = Challenge.objects.filter (category__in=sample_set).count ()
                expected_category_names = list (ChallengeCategory.objects.filter (pk__in=sample_set).values_list ('name', flat=True))
                sample_set = ','.join (sample_set)

                url = reverse_with_query ('api.challenges:challenge-list', query_params={'category_ids': sample_set})
                response = this.client.get (url)

                this.assertEqual (len (response.data), expected_count)
                for challenge in response.data:
                    this.assertIn (challenge ['category'] ['name'], expected_category_names)

        for i in range (3):
            for sample_set in [random.sample ([str (pk) for pk in range (10, 32)], k) for k in range (1, 6)]:
                sample_set = ','.join (sample_set)

                url = reverse_with_query ('api.challenges:challenge-list', query_params={'category_ids': sample_set})
                response = this.client.get (url)

                this.assertEqual (len (response.data), 0)

    @anonymous_api_user_test
    def test_challenge_list_name_filter_api_response (this):
        for (search_string, expected_count) in [('tHe', 3), ('aNd', 2), ('oN', 3), ('bIlLs', 1), ('oWn', 3)]:
            url = reverse_with_query ('api.challenges:challenge-list', query_params={'name_pattern': search_string})
            response = this.client.get (url)
            this.assertEqual (len (response.data), expected_count, msg=f"search: {search_string}")

        for search_string in ['schmutz', 'punim', 'kvetch', 'vantz', 'schlemiel']:
            url = reverse_with_query ('api.challenges:challenge-list', query_params={'name_pattern': search_string})
            response = this.client.get (url)
            this.assertEqual (len (response.data), 0)

    @anonymous_api_user_test
    def test_challenge_list_categories_name_filter_api_response (this):
        for (category_ids, search_string, expected_count) in [('4,6', 'tHe', 2), ('1,2,7,6', 'aNd', 2), ('4,5,8', 'oN', 2), ('4,5,9', 'bIlLs', 1), ('1,7,9', 'oWn', 1)]:
            url = reverse_with_query ('api.challenges:challenge-list', query_params={'category_ids': category_ids, 'name_pattern': search_string})
            response = this.client.get (url)
            this.assertEqual (len (response.data), expected_count, msg=f"search: {search_string}")

    @anonymous_api_user_test
    def test_challenge_detail_api_status_200 (this):
        for pk in random.sample (list (Challenge.objects.all ().values_list (flat=True)), 5):
            url = reverse_with_query ('api.challenges:challenge-detail', query_params={'challenge_id': pk})
            response = this.client.get (url)

            this.assertEqual (response.status_code, status.HTTP_200_OK, msg=f"failed with pk={pk}")

    @anonymous_api_user_test
    def test_challenge_detail_api_status_404 (this):
        largest_pk = Challenge.objects.all ().order_by ('-pk').values_list ('pk', flat=True).first ()

        for pk in random.sample (list (range (largest_pk + 1, largest_pk + 100)), 5):
            url = reverse_with_query ('api.challenges:challenge-detail', query_params={'challenge_id': pk})
            response = this.client.get (url)

            this.assertEqual (response.status_code, status.HTTP_404_NOT_FOUND, msg=f"failed with pk={pk}")

    @anonymous_api_user_test
    def test_obstacle_detail_api_status_200 (this):
        for pk in random.sample (list (Obstacle.objects.all ().values_list (flat=True)), 5):
            url = reverse_with_query ('api.challenges:obstacle-detail', query_params={'obstacle_id': pk})
            response = this.client.get (url)

            this.assertEqual (response.status_code, status.HTTP_200_OK, msg=f"failed with pk={pk}")

    @anonymous_api_user_test
    def test_obstacle_detail_api_status_404 (this):
        for pk in random.sample (list (range (0, 7)) + list (range (70, 128)), 5):
            url = reverse_with_query ('api.challenges:obstacle-detail', query_params={'obstacle_id': pk})
            response = this.client.get (url)

            this.assertEqual (response.status_code, status.HTTP_404_NOT_FOUND, msg=f"failed with pk={pk}")
