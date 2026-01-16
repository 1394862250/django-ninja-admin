from django.db import migrations

def init_settings(apps, schema_editor):
    from apps.setting.services import initialize_system_settings
    initialize_system_settings()

def reverse_init_settings(apps, schema_editor):
    SystemSetting = apps.get_model('setting', 'SystemSetting')
    SystemSetting.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(init_settings, reverse_init_settings),
    ]
