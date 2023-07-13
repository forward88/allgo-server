from django.db import models
from django.utils.html import format_html

class ChallengeCategory (models.Model):
    class Meta:
        verbose_name = "Challenge Category"
        verbose_name_plural = "Challenge Categories"

    name = models.CharField (max_length = 64)
    icon_emoji = models.CharField (max_length = 4)

    def large_icon (this):
        return format_html ("<span style='font-size: 300%;'>{}</span>".format (this.icon_emoji))

    def __str__ (this):
        return this.name
