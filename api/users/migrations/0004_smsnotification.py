# Generated by Django 3.2.8 on 2022-01-26 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_create_user_obstacle_view'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('TEAM_INVITATION', 'Team Invitation')], max_length=64, unique=True)),
                ('message_body', models.TextField()),
            ],
            options={
                'verbose_name': 'SMS Notification',
            },
        ),
    ]
