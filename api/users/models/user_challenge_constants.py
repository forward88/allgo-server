from django.db import models
from django.utils.functional import classproperty

__all__ = ['UserChallengeState', 'UserChallengeAction']

class UserChallengeState (models.TextChoices):
    ACTIVE = ('A', 'Active')
    PAUSED = ('P', 'Paused')
    COMPLETED = ('C', 'Completed')
    LEFT = ('L', 'Left')
    EXPIRED = ('E', 'Expired')

class UserChallengeAction (models.TextChoices):
    JOIN = ('J', 'Join')
    PAUSE = ('P', 'Pause')
    UNPAUSE = ('U', 'Unpause')
    LEAVE = ('L', 'Leave')
    COMPLETE = ('C', 'Complete')
    EXPIRE = ('E', 'Expire')

    __corresponding_states__ = {
        'JOIN': UserChallengeState.ACTIVE,
        'PAUSE': UserChallengeState.PAUSED,
        'UNPAUSE': UserChallengeState.ACTIVE,
        'LEAVE': UserChallengeState.LEFT,
        'COMPLETE': UserChallengeState.COMPLETED,
        'EXPIRE': UserChallengeState.EXPIRED }

    @classproperty
    def client_actions (cls):
        return ['JOIN', 'PAUSE', 'UNPAUSE', 'LEAVE']

    @property
    def state (this):
        return this.__corresponding_states__ [this.name]
