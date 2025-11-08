"""
API响应格式工具
"""
from typing import Any, Optional, Dict, List
from django.http import JsonResponse, HttpRequest
from django.contrib.auth.models import User


class ApiResponse:
    """统一的API响应格式"""
    
    def __init__(self, data: Any = None, message: str = "", success: bool = True, status_code: int = 200):
        self.data = data
        self.message = message
        self.success = success
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        response = {
            'success': self.success,
            'message': self.message,
            'data': self.data
        }
        return response
    
    def to_json_response(self) -> JsonResponse:
        """转换为Django JsonResponse"""
        return JsonResponse(
            data=self.to_dict(),
            status=self.status_code,
            safe=isinstance(self.data, (dict, list))
        )


class SuccessResponse(ApiResponse):
    """成功响应"""
    
    def __init__(self, data: Any = None, message: str = "操作成功"):
        super().__init__(data=data, message=message, success=True, status_code=200)


class CreatedResponse(ApiResponse):
    """创建成功响应"""
    
    def __init__(self, data: Any = None, message: str = "创建成功"):
        super().__init__(data=data, message=message, success=True, status_code=201)


class BadRequestResponse(ApiResponse):
    """400错误响应"""
    
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(data=None, message=message, success=False, status_code=400)


class UnauthorizedResponse(ApiResponse):
    """401错误响应"""
    
    def __init__(self, message: str = "未授权访问"):
        super().__init__(data=None, message=message, success=False, status_code=401)


class ForbiddenResponse(ApiResponse):
    """403错误响应"""
    
    def __init__(self, message: str = "禁止访问"):
        super().__init__(data=None, message=message, success=False, status_code=403)


class NotFoundResponse(ApiResponse):
    """404错误响应"""
    
    def __init__(self, message: str = "资源不存在"):
        super().__init__(data=None, message=message, success=False, status_code=404)


class ServerErrorResponse(ApiResponse):
    """500错误响应"""
    
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(data=None, message=message, success=False, status_code=500)


class PaginatedResponse:
    """分页响应格式"""
    
    def __init__(self, objects_list: List[Any], page: int = 1, page_size: int = 10, total_count: int = None):
        self.objects_list = objects_list
        self.page = page
        self.page_size = page_size
        self.total_count = total_count or len(objects_list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为分页字典格式"""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        
        return {
            'success': True,
            'message': '获取成功',
            'data': {
                'results': self.objects_list,
                'pagination': {
                    'page': self.page,
                    'page_size': self.page_size,
                    'total_count': self.total_count,
                    'total_pages': total_pages,
                    'has_next': self.page < total_pages,
                    'has_previous': self.page > 1
                }
            }
        }
    
    def to_json_response(self) -> JsonResponse:
        """转换为Django JsonResponse"""
        return JsonResponse(self.to_dict())


def handle_exception(exc: Exception) -> ApiResponse:
    """异常处理辅助函数"""
    import traceback
    
    # 开发环境下显示详细错误信息
    import os
    if os.environ.get('DEBUG', 'False').lower() == 'true':
        error_detail = traceback.format_exc()
    else:
        error_detail = str(exc)
    
    return ServerErrorResponse(message=f"操作失败: {error_detail}")


def check_user_exists(user_id: int) -> Optional[User]:
    """检查用户是否存在"""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None