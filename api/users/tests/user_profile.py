import random, uuid
from unittest.mock import patch

from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from schoolyard.tests import reverse_with_query
from api.scoring.models import SupplementalXPReward
from ...rest_auth.tests import anonymous_api_user_test, active_api_user_test, set_access_token_header
from ...rest_auth.utils import create_access_token
from ..models import APIUser, UserProfile
from ..serializers import UserSerializerErrorMessage

__all__ = ['UserTests', 'NicknameTests']

ERROR_DETAIL_KEY = settings.REST_FRAMEWORK ['NON_FIELD_ERRORS_KEY']

class UserTests (APITestCase):
    fixtures = ['testing/users-mixed']

    @anonymous_api_user_test
    def test_sign_in_new_user (this):
        sign_in_url = reverse ('api.rest_auth:sign-in')

        test_phone_number = f"+1612555{random.randrange (1000,9999)}"

        api_user_count_0 = APIUser.objects.all ().count ()
        user_profile_count_0 = UserProfile.objects.all ().count ()

        post_data = {'phone_number': test_phone_number, 'verification_token': '811348'}
        response = this.client.post (sign_in_url, post_data, format='json')

        this.assertEqual (response.status_code, status.HTTP_200_OK)

        api_user_count_1 = APIUser.objects.all ().count ()
        user_profile_count_1 = UserProfile.objects.all ().count ()

        this.assertEqual (api_user_count_0 + 1, api_user_count_1)
        this.assertEqual (user_profile_count_0, user_profile_count_1)

class NicknameTests (APITestCase):
    fixtures = ['testing/users-mixed']

    # Nickname availability tests

    def validate_check_nickname_availablity (this, test_nickname, expected_availability):
        url = reverse_with_query ('api.users:check-nickname-availability', query_params={'nickname': test_nickname})

        response = this.client.get (url)

        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertEqual (response.data ['nickname_available'], expected_availability)

    @active_api_user_test
    def test_check_nickname_availability_new_nickname (this):
        this.validate_check_nickname_availablity ('ScoobyDoo', True)

    @active_api_user_test
    def test_check_nickname_availability_existing_nickname (this):
        test_nickname = UserProfile.objects.filter (nickname__isnull=False).first ().nickname

        this.validate_check_nickname_availablity (test_nickname, False)
        this.validate_check_nickname_availablity (test_nickname.swapcase (), False)

    # Nickname reservation tests

    def validate_claim_nickname (this, test_nickname, success_expected, expected_msg=None):
        api_user_count_0 = APIUser.objects.all ().count ()
        user_profile_count_0 = UserProfile.objects.all ().count ()

        url = reverse_with_query ('api.users:claim-nickname', query_params={'nickname': test_nickname})
        response = this.client.get (url)

        api_user_count_1 = APIUser.objects.all ().count ()
        user_profile_count_1 = UserProfile.objects.all ().count ()

        this.assertEqual (api_user_count_0, api_user_count_1)

        if success_expected:
            this.assertEqual (response.status_code, status.HTTP_200_OK)
            this.assertEqual (user_profile_count_0 + 1, user_profile_count_1)

        else:
            this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
            this.assertEqual (user_profile_count_0, user_profile_count_1)
            this.assertEqual (response.data [ERROR_DETAIL_KEY] [0], expected_msg)

    def test_claim_nickname_new (this):
        access_token = create_access_token (uuid.UUID ('af2f0005-a681-4c87-99d2-df113479da66'))
        set_access_token_header (this.client, access_token)

        this.validate_claim_nickname ('ScoobyDoo', True)

        expected_xp = SupplementalXPReward.objects.get(
            reward_type=SupplementalXPReward.RewardType.ONBOARDING_COMPLETE
        ).xp_value
        user_profile = UserProfile.objects.get(nickname='ScoobyDoo')
        this.assertEqual(user_profile.xp_earned, expected_xp)

    def test_claim_nickname_already_claimed (this):
        access_token = create_access_token (uuid.UUID ('b4a63057-25a9-40db-84ad-382c19dfc30f'))
        set_access_token_header (this.client, access_token)

        this.validate_claim_nickname ('ScoobyDoo', False, expected_msg=UserSerializerErrorMessage.USER_HAS_NICKNAME.value)

    def test_claim_nickname_existing_nicknames (this):
        test_nickname = UserProfile.objects.filter (nickname__isnull=False).first ().nickname

        access_token = create_access_token (uuid.UUID ('af2f0005-a681-4c87-99d2-df113479da66'))
        set_access_token_header (this.client, access_token)

        this.validate_claim_nickname (test_nickname, False, expected_msg=UserSerializerErrorMessage.NICKNAME_CLAIMED.value)
        this.validate_claim_nickname (test_nickname.swapcase (), False, expected_msg=UserSerializerErrorMessage.NICKNAME_CLAIMED.value)


def expected_profile_data(profile: UserProfile) -> dict:
    return {
        "nickname": profile.nickname,
        "user_id": str(profile.api_user.pk),
        "team_uid": None,
        "avatar": None,
        "background_color": None,
        "streak": 0,
        "xp_earned": None,
        "chat_user_id": profile.chat_user_id,
    }


class UserDetailTests(APITestCase):
    fixtures = ['testing/users-mixed']

    @active_api_user_test
    def test_self_details(self):
        profile: UserProfile = self.api_user.user_profile
        url = reverse("api.users:user-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_profile_data(profile))

        profile = random.choice(UserProfile.objects.exclude(pk=profile.pk))
        url = reverse_with_query(
            "api.users:user-detail",
            query_params={"user_id": profile.api_user.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_profile_data(profile))
