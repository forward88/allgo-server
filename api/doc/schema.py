from drf_spectacular.openapi import build_basic_type, OpenApiTypes
from drf_spectacular.extensions import OpenApiSerializerFieldExtension

class DurationFieldExtension (OpenApiSerializerFieldExtension):
    target_class = 'rest_framework.fields.DurationField'

    def map_serializer_field (this, auto_schema, direction):
        return {'type': 'string', 'default': '[DD] [HH:[MM:]]ss[.uuuuuu]'}
