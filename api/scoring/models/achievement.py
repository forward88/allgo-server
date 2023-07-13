from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from django.templatetags.static import static

from schoolyard.models import RelativeFilePathModelField, LOCAL_ASSET_ROOT

ASSET_DIR = 'scoring/assets/achievements'

def color_asset_path ():
    return LOCAL_ASSET_ROOT / ASSET_DIR / 'color'

def grey_asset_path ():
    return LOCAL_ASSET_ROOT / ASSET_DIR / 'grey'

class Achievement (models.Model):
    name = models.CharField (max_length=64)
    color_image = RelativeFilePathModelField (path=color_asset_path, match='.*.png', max_length=1024)
    grey_image = RelativeFilePathModelField (path=grey_asset_path, match='.*.png', max_length=1024)
    order_rank = models.PositiveSmallIntegerField ()

    def __str__ (this):
        return this.name

    def get_image_src (this, color):
        return static (this.color_image if color else this.grey_image)

    def get_image_html (this, color):
        return format_html (f"<img src='{this.get_image_src (color)}'/>")

    @property
    def color_image_src (this):
        return this.get_image_src (True)

    @property
    def grey_image_src (this):
        return this.get_image_src (False)

    @property
    @admin.display (description="Color")
    def color_image_sample (this):
        return this.get_image_html (True)

    @property
    @admin.display (description="Grey")
    def grey_image_sample (this):
        return this.get_image_html (False)
