"""
用户模型的信号处理器
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建用户资料"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except Exception as e:
            # 如果创建失败，记录错误但不阻止用户创建
            print(f"创建用户资料失败: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """用户更新时自动保存用户资料"""
    if hasattr(instance, 'profile'):
        try:
            instance.profile.save()
        except Exception as e:
            print(f"保存用户资料失败: {e}")