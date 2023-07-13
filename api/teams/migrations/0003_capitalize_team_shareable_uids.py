from django.db import migrations

class Migration (migrations.Migration):
    dependencies = [('teams', '0002_initial')]

    operations = [
        migrations.RunSQL (
            'UPDATE "teams_team" SET "shareable_uid" = UPPER("shareable_uid");',
            reverse_sql='UPDATE "teams_team" SET "shareable_uid" = LOWER("shareable_uid");') ]
