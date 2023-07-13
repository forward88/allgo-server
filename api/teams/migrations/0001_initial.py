# Generated by Django 3.2.8 on 2022-01-18 09:30

import api.teams.models.team
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shareable_uid', models.CharField(default=api.teams.models.team.generate_shareable_uid, max_length=8, unique=True)),
                ('user_created', models.BooleanField()),
                ('ctime', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
        ),
        migrations.CreateModel(
            name='TeamInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('P', 'Pending'), ('A', 'Accepted'), ('D', 'Declined')], default='P', max_length=1)),
                ('ctime', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
        ),
    ]