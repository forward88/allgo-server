from django.db import models

class UserXPLevel (models.Model):
    class Meta:
        verbose_name = "User XP Level"

    level = models.PositiveIntegerField ()
    xp_threshold = models.PositiveIntegerField (verbose_name='XP Threshold')

    def __str__ (this):
        return f"Level {this.level} ({this.xp_threshold})"
