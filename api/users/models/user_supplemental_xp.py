from django.db import models

__all__ = ['UserSupplementalXP']

class UserSupplementalXP (models.Model):
    user_profile = models.ForeignKey ("users.UserProfile", on_delete=models.CASCADE, related_name="supplemental_xps")
    supplemental_xp_reward = models.ForeignKey ("scoring.SupplementalXPReward", on_delete=models.CASCADE)
    ctime = models.DateTimeField (auto_now_add=True)

    class Meta:
        verbose_name = "User Supplemental XP"
        verbose_name_plural = "Users Supplemental XP"

    def __str__ (this):
        return f"{this.user_profile.nickname}: {this.supplemental_xp_reward.reward_type}:{this.supplemental_xp_reward.xp_value}"
