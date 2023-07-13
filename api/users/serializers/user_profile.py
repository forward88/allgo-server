import enum
from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework import serializers

from api.users.models import UserProfile, APIUserHasNicknameException, UserColorProfile, Avatar, APIUser
from api.challenges.models import Challenge
from api.challenges.serializers import NestedChallengeCategorySerializer

__all__ = ['CheckNicknameAvailabilitySerializer', 'ClaimNicknameSerializer',
           'UserProfileDetailSerializer', 'UserSerializerErrorMessage',
           'UserProfileOptionsSerializer', 'UserProfileEditSerializer',
           'UserAccountDeleteSerializer']


class UserSerializerErrorMessage (enum.Enum):
    USER_HAS_NICKNAME = "User has already claimed a nickname."
    NICKNAME_CLAIMED = "Nickname has already been claimed."
    SENDBIRD_ERROR = "Error creating sendbird token: {}"

class NicknameSerializer (serializers.Serializer):
    nickname = serializers.CharField (write_only=True, max_length=UserProfile._meta.get_field ('nickname').max_length)

class CheckNicknameAvailabilitySerializer (NicknameSerializer):
    nickname_available = serializers.BooleanField (read_only=True)

    def validate (this, data):
        return {'nickname_available': UserProfile.objects.check_nickname_availability (**data)}

class ClaimNicknameSerializer (NicknameSerializer):
    nickname_claimed = serializers.BooleanField (read_only=True)

    def validate (this, data):
        api_user = this.context ['user']

        try:
            api_user.claim_nickname (data ['nickname'])
        except APIUserHasNicknameException:
            raise serializers.ValidationError (detail=UserSerializerErrorMessage.USER_HAS_NICKNAME.value)
        except IntegrityError:
            raise serializers.ValidationError (detail=UserSerializerErrorMessage.NICKNAME_CLAIMED.value)

        return {'nickname_claimed': True}


class UserAvatarSerializer (serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = ['name', 'model_asset_src', 'metadata_asset_src', 'static_image_asset_src']

    model_asset_src = serializers.CharField ()
    metadata_asset_src = serializers.CharField ()
    static_image_asset_src = serializers.CharField()


class UserProfileBackgroundColorSerializer (serializers.ModelSerializer):
    class Meta:
        model = UserColorProfile
        fields = ['color_id', 'background_rgb']

    color_id = serializers.IntegerField (read_only=True, source='pk')

class UserProfileOptionsSerializer (serializers.Serializer):
    avatars = UserAvatarSerializer (read_only=True, many=True)
    background_colors = UserProfileBackgroundColorSerializer (read_only=True, many=True)

    def validate (this, data):
        avatars = Avatar.objects.all ()
        bg_colors = UserColorProfile.objects.all ()

        return {
            'avatars': UserAvatarSerializer (avatars, many=True).data,
            'background_colors': UserProfileBackgroundColorSerializer (bg_colors, many=True).data }

class UserProfileDetailSerializer (serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'user_id', 'team_uid', 'avatar', 'background_color', 'streak', 'xp_earned', 'chat_user_id', 'xp_level', 'xp_level_progress']

    user_id = serializers.CharField (source='api_user.pk')
    avatar = UserAvatarSerializer (many=False)
    background_color = UserProfileBackgroundColorSerializer (many=False, source='bg_color')

class UserProfileEditSerializer (serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'avatar_name', 'avatar', 'background_color_id', 'background_color']

    nickname = serializers.CharField (allow_null=True)
    avatar_name = serializers.CharField (allow_null=True, write_only=True)
    background_color_id = serializers.IntegerField (allow_null=True, write_only=True)
    avatar = UserAvatarSerializer (read_only=True)
    background_color = UserProfileBackgroundColorSerializer (read_only=True, source='bg_color')

    def validate (this, data):
        user = this.context ['user']

        if data ['nickname'] is not None:
            user.nickname = data ['nickname']

        if data ['avatar_name'] is not None:
            user.avatar = Avatar.objects.get (name=data ['avatar_name'])

        if data ['background_color_id'] is not None:
            user.bg_color = UserColorProfile.objects.get (pk=data ['background_color_id'])

        try:
            user.save ()
        except IntegrityError:
            raise serializers.ValidationError (detail=UserSerializerErrorMessage.NICKNAME_CLAIMED.value)

        return {
            'nickname': user.nickname,
            'avatar': UserAvatarSerializer (user.avatar).data,
            'background_color': UserProfileBackgroundColorSerializer (user.bg_color).data }


class UserAccountDeleteSerializer(serializers.Serializer):

    def delete(self, instance):
        with transaction.atomic():
            instance.delete()
