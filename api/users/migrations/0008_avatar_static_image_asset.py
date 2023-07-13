import api.users.models.avatar
from django.db import migrations
import schoolyard.models.relative_file_path_model_field

class Migration(migrations.Migration):
    dependencies = [('users', '0007_update_user_obstacle_view')]

    operations = [
        migrations.AddField (
            model_name='avatar',
            name='static_image_asset',
            field=schoolyard.models.relative_file_path_model_field.RelativeFilePathModelField(default='users/assets/avatars/image/dave.png', match='.*.png', max_length=1024, path=api.users.models.avatar.image_asset_path),
            preserve_default=False),
        migrations.RunSQL ("UPDATE users_avatar SET static_image_asset = CONCAT('users/assets/avatars/image/', name, '.png');", reverse_sql="") ]
