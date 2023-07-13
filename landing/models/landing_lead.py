from django.db import models

class LandingLead (models.Model):
    class Meta:
        verbose_name = "Landing Lead"

    email = models.EmailField ()
    device_tag = models.UUIDField ()
    user_agent = models.CharField (max_length = 4096)
    referring_url = models.URLField ()
    ctime = models.DateTimeField (auto_now_add = True)
