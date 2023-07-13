from django.db import models
from django.utils import timezone

__all__ = ['BaseEvent']

class BaseEvent (models.Model):
    ctime = models.DateTimeField (default=timezone.now, verbose_name="Created At")
    api_user = models.ForeignKey ('users.APIUser', on_delete=models.CASCADE)

    class Meta:
        abstract = True
