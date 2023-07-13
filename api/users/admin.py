import random

from django.contrib import admin

from .models import *

class UserProfileInline (admin.StackedInline):
    model = UserProfile
    min_num = 1
    can_delete = False

    fields = ['nickname']

class NoProfileFilter (admin.SimpleListFilter):
    title = "UserProfile status"
    parameter_name = 'has_nickname'

    def lookups (this, request, model_admin):
        return (('false', 'Missing UserProfile'), ('true', 'Linked UserProfile'))

    def queryset (this, request, queryset):
        if this.value () == 'true':
            return queryset.filter (user_profile__isnull=False)

        if this.value () == 'false':
            return queryset.filter (user_profile__isnull=True)

@admin.register (APIUser)
class APIUserAdmin (admin.ModelAdmin):
    inlines = [UserProfileInline]

    list_display = ['__str__', 'phone_number', 'last_access', 'last_sign_in']
    list_filter = [NoProfileFilter]

    fields = (
        'user_id',
        'active',
        'phone_number',
        'last_access',
        ('last_sign_in', 'first_sign_in'),
        'ctime',
        'refresh_token_revocation_cursor')
    readonly_fields = ['user_id', 'last_access', 'last_sign_in', 'first_sign_in', 'ctime']

@admin.register (UserProfile)
class UserProfileAdmin (admin.ModelAdmin):
    list_display = ['nickname', 'xp_earned', 'xp_earned_obstacle', 'xp_earned_supplemental', 'xp_level', 'xp_level_progress']
    fields = ['nickname', 'team', 'bg_color', 'avatar']

class UserChallengePhaseInline (admin.TabularInline):
    model = UserChallengePhase
    extra = 0

class UserObstacleInline (admin.TabularInline):
    model = UserObstacle
    extra = 0
    can_delete = False
    readonly_fields = [ field.name for field in UserObstacle._meta.fields ]

@admin.register (UserChallenge)
class UserChallengeAdmin (admin.ModelAdmin):
    list_display = ['pk', 'user', 'challenge', 'iteration', 'state_label', 'completable']

    inlines = [UserChallengePhaseInline, UserObstacleInline]

@admin.register (SMSNotification)
class SMSNotificationAdmin (admin.ModelAdmin):
    list_display = ['notification_type', 'message_body']

@admin.register (Avatar)
class AvatarAdmin (admin.ModelAdmin):
    list_display = ['name', 'model_asset', 'metadata_asset', 'static_image_asset']

@admin.register (UserColorProfile)
class UserColorProfileAdmin (admin.ModelAdmin):
    list_display = ['closest_css3_color', 'color_sample']

@admin.register (UserSupplementalXP)
class UserSupplementalXPAdmin (admin.ModelAdmin):
    pass
