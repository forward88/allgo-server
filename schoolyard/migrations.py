from django.core.management import call_command
from django.db import migrations

class LoadDataOperation (migrations.RunPython):
    @staticmethod
    def get_forward_func (fixture_paths):
        def forward_command (apps, schema_editor):
            call_command ('loaddata', *fixture_paths)
        return forward_command

    def __init__ (this, fixture_paths):
        super ().__init__ (LoadDataOperation.get_forward_func (fixture_paths), reverse_code=migrations.RunPython.noop)
