from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from ..rest_auth.tests import anonymous_api_user_test

class ScoringTests (APITestCase):
    fixtures = [ 'required/achievements', 'required/user_xp_levels' ]

    @anonymous_api_user_test
    def test_achievements (this):
        url = reverse ('api.scoring:achievement-list')
        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (len (response.data), 15)

        for achievement in response.data:
            this.assertRegex (achievement ['color_image_src'], '.+/color/.+\.png$')
            this.assertRegex (achievement ['grey_image_src'], '.+/grey/.+\.png$')

            base_color_image_src = achievement ['color_image_src'].replace ('color', '')
            base_grey_image_src = achievement ['grey_image_src'].replace ('grey', '')
            this.assertEqual (base_color_image_src, base_grey_image_src)
