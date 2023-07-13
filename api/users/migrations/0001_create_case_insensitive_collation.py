from django.db import migrations
from django.contrib.postgres.operations import CreateCollation

class Migration (migrations.Migration):
    initial = True
    dependencies = []
    operations = [CreateCollation ('case_insensitive', provider='icu', locale='und-u-ks-level2', deterministic=False)]
