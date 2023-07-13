import uuid
from datetime import datetime

from django.db import models, transaction
from django.utils import timezone
from django.core import exceptions
from django.contrib import admin
from phonenumber_field.modelfields import PhoneNumberField

from . import UserSupplementalXP
from api.rest_auth.utils import create_access_refresh_token_pair
from api.scoring.models import SupplementalXPReward
from services import Sendbird

__all__ = ['APIUserState', 'APIUser', 'AnonymousAPIUser', 'APIUserHasNicknameException', 'DeactivatedAPIUserException', 'RevokedTokenException']

class APIUserHasNicknameException (exceptions.BadRequest):
    pass

class DeactivatedAPIUserException (exceptions.BadRequest):
    pass

class RevokedTokenException (exceptions.BadRequest):
    pass

class APIUserManager (models.Manager):
    def load_user_with_phone_number (phone_number):
        (api_user, created) = this.get_or_create (phone_number=phone_number)

        if created:
            pass

class APIUserState (models.TextChoices):
    AUTH_PENDING = ('P', 'Authentication Pending')
    ACTIVE = ('A', 'Active')
    DEACTIVATED = ('D', 'Deactivated')

class APIUser (models.Model):
    class Meta:
        verbose_name = "API User"

    user_id = models.UUIDField (db_column='id', primary_key=True, editable=False, default=uuid.uuid4, verbose_name="User ID")
    phone_number = PhoneNumberField (unique=True)
    state = models.CharField (max_length=1, choices=APIUserState.choices, default=APIUserState.AUTH_PENDING)
    first_sign_in = models.DateTimeField (blank=True, null=True, verbose_name="First Sign In")
    last_sign_in = models.DateTimeField (blank=True, null=True, verbose_name="Last Sign In")
    last_access = models.DateTimeField (blank=True, null=True, verbose_name="Last Access")
    refresh_token_revocation_cursor = models.PositiveIntegerField (default=0, verbose_name="Refresh Token Revocation Cursor")
    ctime = models.DateTimeField (auto_now_add=True, verbose_name="Created At")

    objects = APIUserManager ()

    @property
    def active (this):
        return this.state == APIUserState.ACTIVE

    @property
    def is_authenticated (this):
        return this.active

    @property
    def has_nickname (this):
        return hasattr (this, 'user_profile') and this.user_profile is not None and this.user_profile.nickname is not None

    @property
    def nickname (this):
        if this.has_nickname:
            return this.user_profile.nickname

        return None

    def __str__ (this):
        if not this.has_nickname:
            return str (this.user_id)

        return this.user_profile.nickname

    def sign_in (this):
        if this.state == APIUserState.DEACTIVATED:
            raise DeactivatedAPIUserException ()

        now = timezone.now ()

        this.state = APIUserState.ACTIVE
        this.last_sign_in = now

        if this.first_sign_in is None:
            this.first_sign_in = now

        this.save ()

        return create_access_refresh_token_pair (this.pk, this.refresh_token_revocation_cursor + 1)

    def claim_nickname (this, nickname):
        if hasattr (this,'user_profile') and this.user_profile is not None:
            raise APIUserHasNicknameException ()

        with transaction.atomic ():
            related_model = type (this).user_profile.related.related_model

            this.user_profile = related_model (nickname=nickname)
            this.user_profile.save ()
            this.save ()

            this.add_supplemental_xp (SupplementalXPReward.RewardType.ONBOARDING_COMPLETE)

            Sendbird.create_user (this.user_profile.chat_user_id, this.user_profile.nickname, '')

    def add_supplemental_xp (self, reward_type: SupplementalXPReward.RewardType) -> None:
        reward = SupplementalXPReward.objects.get (reward_type=reward_type)
        UserSupplementalXP.objects.create (
            user_profile=self.user_profile,
            supplemental_xp_reward=reward)

    def update_revocation_cursor (this, revocation_cursor):
        if revocation_cursor <= this.refresh_token_revocation_cursor:
            raise RevokedTokenException ()

        this.refresh_token_revocation_cursor = revocation_cursor
        this.save ()

        return this.refresh_token_revocation_cursor + 1

    def register_access (this):
        if not this.is_authenticated:
            return

        this.last_access = timezone.now ()
        this.save ()

class AnonymousAPIUser:
    is_authenticated = False
