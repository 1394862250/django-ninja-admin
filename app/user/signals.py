"""
用户模型的信号处理器
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import random

def generate_nickname():
    """生成随机昵称：用户{随机五位数字}"""
    random_number = random.randint(10000, 99999)
    return f"用户{random_number}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建用户资料"""
    if created:
        try:
            # 生成唯一昵称
            nickname = generate_nickname()
            while UserProfile.objects.filter(nickname=nickname).exists():
                nickname = generate_nickname()
            
            UserProfile.objects.create(user=instance, nickname=nickname)
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