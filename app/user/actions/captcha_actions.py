"""
验证码相关的原子操作
所有 Action 必须 < 30 行，单一职责，无流程控制
"""
from captcha.models import CaptchaStore


def delete_captcha(captcha_store: CaptchaStore):
    """删除验证码"""
    captcha_store.delete()
