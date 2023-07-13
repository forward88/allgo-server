from django.urls import path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import schema

app_name = 'api.doc'
urlpatterns = [
    path ('', SpectacularSwaggerView.as_view (url_name='api.doc:schema'), name='ui'),
    path ('schema/', SpectacularAPIView.as_view (), name='schema') ]

def openapi_preprocess_exclude_schema (endpoints, **kwargs):
    return [(path, *args) for (path, *args) in endpoints if path != '/api/doc/schema/']
