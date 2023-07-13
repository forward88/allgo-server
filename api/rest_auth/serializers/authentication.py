import enum

import jwt
from django.db import models
from django.conf import settings
from django.core import exceptions as django_exceptions
from rest_framework import serializers, exceptions as rf_exceptions
from phonenumber_field import serializerfields

from api.users.models import APIUser, APIUserState, UserProfile, DeactivatedAPIUserException, RevokedTokenException
from api.rest_auth.utils import request_otp, validate_otp, extract_refresh_token_data, rotate_refresh_token

__all__ = ['RequestPhoneVerificationSerializer', 'SignInSerializer', 'RefreshTokensSerializer', 'APIAuthErrorMessage']

class APIAuthErrorMessage (enum.Enum):
    INVALID_OTP = "Invalid `verification_token` provided."
    INVALID_PHONE_NUMBER = "Invalid phone number"
    DEACTIVATED_USER = "User has been deactivated."
    REVOKED_TOKEN = "Provided token has been revoked."
    EXPIRED_TOKEN = "Provided token has expired."
    INVALID_TOKEN = "Provided token is invalid."

class PhoneNumberSerializerField (serializerfields.PhoneNumberField):
    default_error_messages = {'invalid': APIAuthErrorMessage.INVALID_PHONE_NUMBER.value}

    def to_representation (this, value):
        return str (value)

class RequestPhoneVerificationSerializer (serializers.Serializer):
    phone_number = PhoneNumberSerializerField (write_only=True)
    request_successful = serializers.BooleanField (read_only=True)

    def validate (this, data):
        request_otp (data ['phone_number'])

        return {'request_successful': True}

class SignInSerializer (serializers.Serializer):
    phone_number = PhoneNumberSerializerField (write_only=True)
    verification_token = serializers.CharField (write_only=True, min_length=settings.API_AUTH_OTP_LENGTH, max_length=settings.API_AUTH_OTP_LENGTH)
    access_token = serializers.CharField (read_only=True)
    refresh_token = serializers.CharField (read_only=True)
    new_user = serializers.BooleanField (read_only=True)
    nickname = serializers.CharField (read_only=True, max_length=UserProfile._meta.get_field ('nickname').max_length)

    def validate (this, data):
        if not validate_otp (data ['phone_number'], data ['verification_token']):
            raise rf_exceptions.ValidationError (detail=APIAuthErrorMessage.INVALID_OTP.value)

        (api_user, created) = APIUser.objects.get_or_create (phone_number=data ['phone_number'])

        try:
            (access_token, refresh_token) = api_user.sign_in ()
        except DeactivatedAPIUserException:
            raise rf_exceptions.NotAuthenticated (detail=APIAuthErrorMessage.DEACTIVATED_USER.value)

        return {"access_token": access_token, "refresh_token": refresh_token, "new_user": created, "nickname": api_user.nickname}

class RefreshTokensSerializer (serializers.Serializer):
    access_token = serializers.CharField (read_only=True)
    refresh_token = serializers.CharField (max_length=1024)

    def validate (this, data):
        try:
            (sub_uuid, revocation_cursor, expiration) = extract_refresh_token_data (data ['refresh_token'])
        except jwt.exceptions.ExpiredSignatureError:
            raise rf_exceptions.AuthenticationFailed (detail=APIAuthErrorMessage.EXPIRED_TOKEN.value)
        except jwt.exceptions.InvalidTokenError:
            raise rf_exceptions.AuthenticationFailed (detail=APIAuthErrorMessage.INVALID_TOKEN.value)

        try:
            api_user = APIUser.objects.get (pk=sub_uuid, state=APIUserState.ACTIVE)
        except APIUser.DoesNotExist:
            raise rf_exceptions.NotAuthenticated (detail=this.NONEXISTENT_USER_ERROR_MSG)

        try:
            new_revocation_cursor = api_user.update_revocation_cursor (revocation_cursor)
        except RevokedTokenException:
            raise rf_exceptions.AuthenticationFailed (detail=APIAuthErrorMessage.REVOKED_TOKEN.value)

        (access_token, refresh_token) = rotate_refresh_token (api_user.pk, new_revocation_cursor, expiration)

        return {"access_token": access_token, "refresh_token": refresh_token}
