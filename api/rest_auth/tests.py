import random, functools
from datetime import date, timedelta

import jwt, freezegun

from django.urls import reverse
from django.conf import settings
from django.test import tag
from django.utils import timezone
from django.utils.functional import classproperty
from rest_framework import status, exceptions
from rest_framework.test import APITestCase

from api.users.models import APIUser, APIUserState
from .utils import extract_access_token_data, extract_refresh_token_data, create_access_token
from .serializers import APIAuthErrorMessage
from .authentication import APIKeyAuthentication, JWTAuthentication, JWTAuthErrorMessage

API_KEY_HEADER_KEY = "HTTP_" + APIKeyAuthentication.API_KEY_HTTP_HEADER
ACCESS_TOKEN_HEADER_KEY = "HTTP_" + JWTAuthentication.ACCESS_TOKEN_HTTP_HEADER

def set_api_key_header (api_client, api_key):
    if api_key is None:
        api_key = settings.API_AUTH_ANONYMOUS_KEY

    credential = {API_KEY_HEADER_KEY: api_key}
    api_client.credentials (**credential)

def set_access_token_header (api_client, access_token):
    credential = {ACCESS_TOKEN_HEADER_KEY: JWTAuthentication.ACCESS_TOKEN_HEADER_TYPE + ' ' + access_token}
    api_client.credentials (**credential)

def set_active_api_credentials (test_object, api_user):
    access_token = create_access_token (api_user.pk)
    set_access_token_header (test_object.client, access_token)

def anonymous_api_user_test (test_func):
    @functools.wraps (test_func)
    def wrapper (*args, **kwargs):
        wrapped_this = args [0]

        set_api_key_header (wrapped_this.client, None)

        test_func (*args, **kwargs)

    return wrapper

def active_api_user_test (test_func):
    @functools.wraps (test_func)
    def wrapper (*args, **kwargs):
        wrapped_this = args [0]
        wrapped_this.api_user = random.choice (APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False))

        set_active_api_credentials (wrapped_this, wrapped_this.api_user)

        test_func (*args, **kwargs)

    return wrapper

class APIKeyTests (APITestCase):
    test_url = reverse ('api.challenges:challenge-category-list')

    def validate_test_url_response (this, status_code, exception):
        response = this.client.get (this.test_url)

        this.assertEqual (response.status_code, status_code)

        if exception is not None:
            this.assertEqual (response.data ['detail'], exception.default_detail)

    @anonymous_api_user_test
    def test_valid_api_key (this):
        this.validate_test_url_response (status.HTTP_200_OK, None)

    def test_invalid_api_key (this):
        set_api_key_header (this.client, api_key=reversed (settings.API_AUTH_ANONYMOUS_KEY))

        this.validate_test_url_response (status.HTTP_401_UNAUTHORIZED, exceptions.AuthenticationFailed)

    def test_missing_api_key (this):
        this.validate_test_url_response (status.HTTP_401_UNAUTHORIZED, exceptions.NotAuthenticated)

class TokenCreationTests (APITestCase):
    fixtures = ['testing/users-mixed']

    error_detail_key = settings.REST_FRAMEWORK ['NON_FIELD_ERRORS_KEY']
    sign_in_url = reverse ('api.rest_auth:sign-in')
    refresh_tokens_url = reverse ('api.rest_auth:refresh-tokens')

    # Access token tests

    @anonymous_api_user_test
    def test_request_otp (this):
        url = reverse ('api.rest_auth:request-phone-verification')

        # invalid phone number
        response = this.client.post (url, {'phone_number': '+1134'}, format='json')

        this.assertEqual (response.status_code, status.HTTP_400_BAD_REQUEST)
        this.assertEqual (response.data ['phone_number'] [0], APIAuthErrorMessage.INVALID_PHONE_NUMBER.value)

        # valid (mock) phone number
        response = this.client.post (url, {'phone_number': '+16125551234'}, format='json')

        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertTrue (response.data ['request_successful'])

    def validate_sign_in_response_failure (this, post_data, expected_status_code, expected_error_msg):
        response = this.client.post (this.sign_in_url, post_data, format='json')

        this.assertEqual (response.status_code, expected_status_code)

        if type (response.data [this.error_detail_key]) == list:
            this.assertEqual (response.data [this.error_detail_key] [0], expected_error_msg)
        else:
            this.assertEqual (response.data [this.error_detail_key], expected_error_msg)

    @anonymous_api_user_test
    def test_sign_in_inactive_user (this):
        test_user = APIUser.objects.exclude (state=APIUserState.ACTIVE).first ()
        post_data = {'phone_number': str (test_user.phone_number), 'verification_token': '811348'}

        this.validate_sign_in_response_failure (post_data, status.HTTP_401_UNAUTHORIZED, APIAuthErrorMessage.DEACTIVATED_USER.value)

    @anonymous_api_user_test
    def test_sign_in_invalid_otp (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE).first ()
        post_data = {'phone_number': str (test_user.phone_number), 'verification_token': '711348'}

        this.validate_sign_in_response_failure (post_data, status.HTTP_400_BAD_REQUEST, APIAuthErrorMessage.INVALID_OTP.value)

    def validate_sign_in_response_success (this, test_user):
        post_data = {'phone_number': str (test_user.phone_number), 'verification_token': '811348'}

        existing_last_sign_in = test_user.last_sign_in

        response = this.client.post (this.sign_in_url, post_data, format='json')

        test_user = APIUser.objects.get (pk=test_user.pk)

        this.assertEqual (response.status_code, status.HTTP_200_OK)
        this.assertIsNotNone (test_user.first_sign_in)
        this.assertIsNotNone (test_user.last_sign_in)
        this.assertNotEqual (existing_last_sign_in, test_user.last_sign_in)

        access_token = response.data ['access_token']
        this.assertEqual (extract_access_token_data (access_token), test_user.pk)

        refresh_token = response.data ['refresh_token']
        (sub_uuid, revocation_cursor, expiration) = extract_refresh_token_data (refresh_token)
        this.assertEqual (sub_uuid, test_user.pk)
        this.assertEqual (revocation_cursor, test_user.refresh_token_revocation_cursor + 1)

    @anonymous_api_user_test
    def test_first_sign_in (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE, first_sign_in__isnull=True).first ()
        this.validate_sign_in_response_success (test_user)

    @anonymous_api_user_test
    def test_nth_sign_in (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE, first_sign_in__isnull=False).first ()
        this.validate_sign_in_response_success (test_user)

    @anonymous_api_user_test
    def test_access_token_expirations (this):
        import time
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE).first ()
        post_data = {'phone_number': str (test_user.phone_number), 'verification_token': '811348'}

        creation_offset_s = settings.API_AUTH_REFRESH_TOKEN_LIFETIME_S + 1
        valid_access_offset_s = creation_offset_s - (settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S - 1)
        expired_access_offset_s = creation_offset_s - (settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S + 1)
        valid_refresh_offset_s = creation_offset_s - (settings.API_AUTH_REFRESH_TOKEN_LIFETIME_S - 1)

        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=creation_offset_s))
        mock_date.start ()
        response = this.client.post (this.sign_in_url, post_data, format='json')
        mock_date.stop ()

        access_token = response.data ['access_token']
        refresh_token = response.data ['refresh_token']

        # Should not fail with exception
        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=valid_access_offset_s))
        mock_date.start ()
        extract_access_token_data (access_token)
        mock_date.stop ()

        # Should fail
        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=expired_access_offset_s))
        mock_date.start ()
        with this.assertRaises (jwt.exceptions.ExpiredSignatureError):
            extract_access_token_data (access_token)
        mock_date.stop ()

        # Should not fail with exception
        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=valid_refresh_offset_s))
        mock_date.start ()
        extract_refresh_token_data (refresh_token)
        mock_date.stop ()

        # Should fail
        with this.assertRaises (jwt.exceptions.ExpiredSignatureError):
            extract_refresh_token_data (refresh_token)

    # Refresh token tests

    def refresh_tokens (this, test_user):
        post_data = {'phone_number': str (test_user.phone_number), 'verification_token': '811348'}
        response = this.client.post (this.sign_in_url, post_data, format='json')

        return (response.data ['access_token'], response.data ['refresh_token'])

    @anonymous_api_user_test
    def test_refresh_access_token_valid (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE).first ()
        (access_token, refresh_token_0) = this.refresh_tokens (test_user)
        revocation_cursor_0 = test_user.refresh_token_revocation_cursor

        (payload_user_id, revocation_tag_0, expiration_0) = extract_refresh_token_data (refresh_token_0)

        post_data = {'refresh_token': refresh_token_0}
        response = this.client.post (this.refresh_tokens_url, post_data, format='json')
        this.assertEqual (response.status_code, status.HTTP_200_OK)

        refresh_token_1 = response.data ['refresh_token']
        (payload_user_id, revocation_tag_1, expiration_1) = extract_refresh_token_data (refresh_token_1)

        test_user = APIUser.objects.get (pk=test_user.pk)
        revocation_cursor_1 = test_user.refresh_token_revocation_cursor

        this.assertEqual (payload_user_id, test_user.pk)
        this.assertEqual (expiration_0, expiration_1)
        this.assertEqual (revocation_tag_0, revocation_cursor_0 + 1)
        this.assertEqual (revocation_tag_1, revocation_cursor_1 + 1)
        this.assertEqual (revocation_tag_1, revocation_tag_0 + 1)

    @anonymous_api_user_test
    def test_refresh_access_token_reuse (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE).first ()
        (access_token, refresh_token) = this.refresh_tokens (test_user)

        post_data = {'refresh_token': refresh_token}

        response = this.client.post (this.refresh_tokens_url, post_data, format='json')
        this.assertEqual (response.status_code, status.HTTP_200_OK)

        response = this.client.post (this.refresh_tokens_url, post_data, format='json')

        this.assertEqual (response.status_code, status.HTTP_401_UNAUTHORIZED)
        this.assertEqual (response.data [this.error_detail_key], APIAuthErrorMessage.REVOKED_TOKEN.value)

    @anonymous_api_user_test
    def test_refresh_token_expirations (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE).first ()

        creation_offset_s = settings.API_AUTH_REFRESH_TOKEN_LIFETIME_S + 1
        valid_access_offset_s = creation_offset_s - (settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S - 1)
        expired_access_offset_s = creation_offset_s - (settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S + 1)

        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=creation_offset_s))
        mock_date.start ()
        (access_token, refresh_token) = this.refresh_tokens (test_user)
        mock_date.stop ()

        # Should not fail with exception
        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=valid_access_offset_s))
        mock_date.start ()
        extract_access_token_data (access_token)
        mock_date.stop ()

        # Should fail
        mock_date = freezegun.freeze_time (timezone.now () - timedelta (seconds=expired_access_offset_s))
        mock_date.start ()
        with this.assertRaises (jwt.exceptions.ExpiredSignatureError):
            extract_access_token_data (access_token)
        mock_date.stop ()

        # Should fail
        post_data = {'refresh_token': refresh_token}
        response = this.client.post (this.refresh_tokens_url, post_data, format='json')
        this.assertEqual (response.status_code, status.HTTP_401_UNAUTHORIZED)
        this.assertEqual (response.data [this.error_detail_key], APIAuthErrorMessage.EXPIRED_TOKEN.value)

class TokenAuthenticationTests (APITestCase):
    fixtures = ['testing/users-mixed']

    test_url = reverse ('api.users:user-detail')
    error_detail_key = settings.REST_FRAMEWORK ['NON_FIELD_ERRORS_KEY']

    def validate_access_token_auth_response (this, status_code, error_msg):
        response = this.client.get (this.test_url)

        this.assertEqual (response.status_code, status_code)

        if error_msg is not None:
            this.assertEqual (response.data [this.error_detail_key], error_msg)

    def test_access_token_authentication_missing (this):
        this.validate_access_token_auth_response (status.HTTP_401_UNAUTHORIZED, exceptions.NotAuthenticated.default_detail)

    @active_api_user_test
    def test_access_token_authentication_valid (this):
        this.validate_access_token_auth_response (status.HTTP_200_OK, None)

    def test_access_token_authentication_invalid (this):
        api_user = random.choice (APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False))
        access_token = create_access_token (api_user.pk)

        set_access_token_header (this.client, access_token.swapcase ())

        this.validate_access_token_auth_response (status.HTTP_401_UNAUTHORIZED, JWTAuthErrorMessage.INVALID_TOKEN.value)

    def test_access_token_authentication_inactive_user (this):
        inactive_user = APIUser.objects.filter (state=APIUserState.DEACTIVATED).first ()
        access_token = create_access_token (inactive_user.pk)
        set_access_token_header (this.client, access_token)

        this.validate_access_token_auth_response (status.HTTP_401_UNAUTHORIZED, exceptions.NotAuthenticated.default_detail)

    def test_access_token_authentication_update_last_access (this):
        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False, last_access__isnull=True).first ()
        access_token = create_access_token (test_user.pk)
        set_access_token_header (this.client, access_token)

        this.client.get (this.test_url)
        test_user = APIUser.objects.get (pk=test_user.pk)
        this.assertIsNotNone (test_user.last_access)

        test_user = APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False, last_access__isnull=False).first ()
        last_access_0 = test_user.last_access
        access_token = create_access_token (test_user.pk)
        set_access_token_header (this.client, access_token)

        this.client.get (this.test_url)
        test_user = APIUser.objects.get (pk=test_user.pk)
        this.assertLess (last_access_0, test_user.last_access)

    def test_access_token_authentication_expired (this):
        api_user = random.choice (APIUser.objects.filter (state=APIUserState.ACTIVE, user_profile__isnull=False))
        offset = timedelta (seconds=settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S + 1)

        mock_date = freezegun.freeze_time (timezone.now () - offset)
        mock_date.start ()
        access_token = create_access_token (api_user.pk)
        mock_date.stop ()

        set_access_token_header (this.client, access_token)

        this.validate_access_token_auth_response (status.HTTP_401_UNAUTHORIZED, JWTAuthErrorMessage.EXPIRED_TOKEN.value)
