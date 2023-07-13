from django.contrib import admin

from .models import *

@admin.register (Achievement)
class AchievementAdmin (admin.ModelAdmin):
    list_display = ['color_image_sample', 'grey_image_sample', 'name', 'color_image', 'grey_image', 'order_rank']
    list_editable = ['name', 'color_image', 'grey_image', 'order_rank']
    list_display_links = ['color_image_sample', 'grey_image_sample']
    ordering = ['order_rank']

@admin.register (UserXPLevel)
class UserXPLevelAdmin (admin.ModelAdmin):
    list_display = ['level', 'xp_threshold']
    list_editable = ['xp_threshold']
    ordering = ['level']

@admin.register (SupplementalXPReward)
class SupplementalXPRewardAdmin (admin.ModelAdmin):
    pass
