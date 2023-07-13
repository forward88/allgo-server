from django.db import models

__all__ = ['SupplementalXPReward']

class SupplementalXPReward (models.Model):
    class RewardType (models.TextChoices):
        ONBOARDING_COMPLETE = ("O", "Onboarding Complete")

    class Meta:
        verbose_name = "Supplemental XP Reward"

    reward_type = models.CharField (max_length=1, choices=RewardType.choices)
    xp_value = models.IntegerField ()
    description = models.TextField ()

    def __str__ (this):
        return f"{this.RewardType (this.reward_type).label}: {this.xp_value} XP"
