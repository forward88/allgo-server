from django.db import models

__all__ = ['ChallengeScoring']

class ChallengeScoring (models.Model):
    challenge = models.OneToOneField ('challenges.Challenge', primary_key=True, on_delete=models.DO_NOTHING, related_name='scoring')
    threshold_sum = models.DecimalField (max_digits=16, decimal_places=3)
    xp_base_unit = models.DecimalField (max_digits=16, decimal_places=3)

    class Meta:
        managed = False
        db_table = 'scoring_challenge_scoring_view'
