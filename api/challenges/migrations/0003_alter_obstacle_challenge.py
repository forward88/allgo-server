# Generated by Django 3.2.8 on 2022-01-28 08:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='obstacle',
            name='challenge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obstacles', to='challenges.challenge'),
        ),
    ]
