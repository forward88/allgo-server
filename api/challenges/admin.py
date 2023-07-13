import random

from django.contrib import admin

from .models import *

@admin.register (ObstacleTask)
class ObstacleTaskAdmin (admin.ModelAdmin):
    list_display = ['plural_name', 'discrete']
    list_editable = ['discrete']

class ObstacleInline (admin.TabularInline):
    model = Obstacle

    fields = ['sequence_rank', 'threshold', 'task', 'discrete', 'interval', 'subcategory']
    readonly_fields = ['discrete']

    extra = 0
    min_num = 1
    radio_fields = {'interval': admin.HORIZONTAL}

    def get_formset (this, *args, **kwargs):
        formset = super ().get_formset (*args, **kwargs)

        for field_name in ['task', 'subcategory']:
            field = formset.form.base_fields [field_name]

            if field_name == 'subcategory':
                field.queryset = ChallengeCategory.objects.exclude (name = 'Mixed')

            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False

        return formset

@admin.register (Challenge)
class ChallengeAdmin (admin.ModelAdmin):
    list_display = (
        'title_block',
        'category_name',
        'duration_days',
        'xp_value',
        'n_participants',
        'repeated_obstacles',
        'n_obstacles',
        'threshold_sum',
        'base_xp_unit',
        'author',
        'ctime')

    fields = (
        ('id'),
        ('name', 'author'),
        'description',
        ('category', 'color_profile'),
        ('duration', 'xp_value'),
        'external_url')
    readonly_fields = ['id']
    radio_fields = {'category': admin.VERTICAL, 'color_profile': admin.VERTICAL}

    inlines = [ObstacleInline]

    def get_form (this, *args, **kwargs):
        form = super ().get_form (*args, **kwargs)

        def quash_fk_mods (field_name):
            field = form.base_fields [field_name]
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False

        quash_fk_mods ("author")
        quash_fk_mods ("category")
        quash_fk_mods ("color_profile")

        color_profile_pks = ChallengeColorProfile.objects.values_list ('pk')
        form.base_fields ["color_profile"].initial = random.choice (color_profile_pks)

        return form

@admin.register (ChallengeCategory)
class ChallengeCategoryAdmin (admin.ModelAdmin):
    list_display = ('name', 'large_icon')

@admin.register (ChallengeColorProfile)
class ChallengeColorProfileAdmin (admin.ModelAdmin):
    list_display = ('closest_css3_color', 'color_sample', 'background_rgb', 'title_rgb', 'description_rgb')
    list_editable = ('background_rgb', 'title_rgb', 'description_rgb')

@admin.register (ChallengeXPBaseline)
class ChallengeXPBaselineAdmin (admin.ModelAdmin):
    list_display = ['challenge_class', 'xp_baseline']
    list_editable = ['xp_baseline']
