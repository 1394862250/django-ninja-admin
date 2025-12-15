"""
验证码相关API接口
包含2个接口：验证码生成、验证码验证
"""

from .base import BaseUserAPI, success_response, error_response
from .captcha_schemas import CaptchaVerifySchema
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

class CaptchaAPI(BaseUserAPI):
    """验证码相关API"""
    
    def _setup_routes(self):
        @self.router.get("/captcha/generate")
        def generate_captcha(request):
            return self._generate_captcha()
        
        @self.router.post("/captcha/verify")
        def verify_captcha(request, data: CaptchaVerifySchema):
            return self._verify_captcha(data)
    
    def _generate_captcha(self):
        """生成验证码图片"""
        try:
            # 生成验证码
            captcha_key = CaptchaStore.pick()
            captcha_image_url_path = captcha_image_url(captcha_key)
            
            return success_response(
                data={
                    'captcha_key': captcha_key,
                    'captcha_image_url': captcha_image_url_path,
                    'expires_in': 300  # 5分钟过期
                },
                message="验证码生成成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"验证码生成失败: {str(exc)}",
                status_code=500
            )
    
    def _verify_captcha(self, data: CaptchaVerifySchema):
        """验证验证码"""
        try:
            # 验证验证码
            captcha_store = CaptchaStore.objects.get(
                hashkey=data.captcha_key,
                response=data.captcha
            )
            # 验证通过后删除验证码记录
            captcha_store.delete()
            
            return success_response(
                data={
                    'valid': True,
                    'message': '验证码正确'
                },
                message="验证码验证成功"
            )
            
        except CaptchaStore.DoesNotExist:
            return error_response(
                message="验证码错误或已过期",
                status_code=400
            )
        except Exception as exc:
            return error_response(
                message=f"验证码验证失败: {str(exc)}",
                status_code=500
            )
