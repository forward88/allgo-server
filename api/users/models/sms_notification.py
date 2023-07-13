from django.db import models

__all__ = ['SMSNotification']

class SMSNotificationType (models.TextChoices):
    TEAM_INVITATION = ('TEAM_INVITATION', 'Team Invitation')

class SMSNotificationManager (models.Manager):
    @property
    def team_invitation_message_body (this):
        return this.get (notification_type=SMSNotificationType.TEAM_INVITATION.value).message_body

class SMSNotification (models.Model):
    notification_type = models.CharField (max_length=64, choices=SMSNotificationType.choices, unique=True)
    message_body = models.TextField ()

    objects = SMSNotificationManager ()

    class Meta:
        verbose_name = "SMS Notification"
