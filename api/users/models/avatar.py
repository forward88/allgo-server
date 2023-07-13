from django.db import models
from django.templatetags.static import static

from schoolyard.models import RelativeFilePathModelField, LOCAL_ASSET_ROOT

ASSET_DIR = 'users/assets/avatars'

def model_asset_path ():
    return LOCAL_ASSET_ROOT / ASSET_DIR / 'model'

def metadata_asset_path ():
    return LOCAL_ASSET_ROOT / ASSET_DIR / 'metadata'

def image_asset_path ():
    return LOCAL_ASSET_ROOT / ASSET_DIR / 'image'

class Avatar (models.Model):
    name = models.CharField (max_length=64, unique=True)
    model_asset = RelativeFilePathModelField (path=model_asset_path, match='.*.glb', max_length=1024)
    metadata_asset = RelativeFilePathModelField (path=metadata_asset_path, match='.*.json', max_length=1024)
    static_image_asset = RelativeFilePathModelField (path=image_asset_path, match='.*.png', max_length=1024)

    def __str__ (this):
        return this.name

    @property
    def model_asset_src (this):
        return static (this.model_asset)

    @property
    def metadata_asset_src (this):
        return static (this.metadata_asset)

    @property
    def static_image_asset_src(self):
        return static(self.static_image_asset)
