"""用户模型信号：自动创建/保存资料。"""
from __future__ import annotations

import random

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .model import UserProfile


def generate_nickname() -> str:
    """生成随机昵称：用户{随机五位数字}。"""
    random_number = random.randint(10000, 99999)
    return f"用户{random_number}"


@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建用户资料。"""
    if not created:
        return
    try:
        nickname = generate_nickname()
        while UserProfile.objects.filter(nickname=nickname).exists():
            nickname = generate_nickname()
        UserProfile.objects.create(user=instance, nickname=nickname)
    except Exception as exc:
        print(f"创建用户资料失败: {exc}")


@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    """用户更新时自动保存用户资料。"""
    if hasattr(instance, "profile"):
        try:
            instance.profile.save()
        except Exception as exc:
            print(f"保存用户资料失败: {exc}")
