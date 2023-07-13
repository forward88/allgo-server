from os.path import relpath

from django.db import models
from django.forms import fields
from django.conf import settings

__all__ = ['LOCAL_ASSET_ROOT', 'RelativeFilePathModelField']

LOCAL_ASSET_ROOT = settings.STATIC_ROOT

class RelativeFilePathFormField (fields.FilePathField):
    def __init__ (this, *args, **kwargs):
        super ().__init__ (*args, **kwargs)

        relative_path_choices = []
        for (absolute_path, filename) in this.choices:
            relative_path_choices.append ((relpath (absolute_path, LOCAL_ASSET_ROOT), filename))

        this.choices = relative_path_choices

class RelativeFilePathModelField (models.FilePathField):
    def formfield (this, *args, **kwargs):
        kwargs ['form_class'] = RelativeFilePathFormField

        return super ().formfield (*args, **kwargs)
