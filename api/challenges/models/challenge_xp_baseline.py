from django.db import models

class ChallengeXPBaseline (models.Model):
    class Meta:
        verbose_name = "Challenge XP Baseline"

    class ChallengeStandardDurationDays (models.IntegerChoices):
        DAY = (1, 'Day')
        WEEK = (7, 'Week')
        MONTH = (28, 'Month')
        YEAR = (365, 'Year')

    class ChallengeDifficulty (models.TextChoices):
        EASY = ('E', 'Easy')
        MEDIUM = ('M', 'Medium')
        HARD = ('H', 'Hard')

    duration_days = models.PositiveIntegerField (choices=ChallengeStandardDurationDays.choices, verbose_name='Duration')
    difficulty = models.CharField (max_length=1, choices=ChallengeDifficulty.choices)
    xp_baseline = models.PositiveIntegerField (verbose_name='XP Baseline')

    @property
    def challenge_class (this):
        return f"{this.ChallengeStandardDurationDays (this.duration_days).label}-{this.ChallengeDifficulty (this.difficulty).label}"

    def __str__ (this):
        return f"{this.challenge_class}:{this.xp_baseline}"
