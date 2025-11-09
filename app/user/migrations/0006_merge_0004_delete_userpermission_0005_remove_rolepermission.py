# Generated migration for merging branches
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_delete_userpermission'),
        ('user', '0005_remove_rolepermission_user_role_permission_unique_and_more'),
    ]

    operations = [
        # 合并迁移：两个分支操作不冲突，可以安全合并
    ]

