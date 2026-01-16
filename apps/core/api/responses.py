"""轻量的 API 响应封装，仅负责格式化输出，不包含业务逻辑。"""
from typing import Any, Dict, List, Optional
from django.http import JsonResponse


class ApiResponse:
    """统一的API响应格式"""

    def __init__(
        self,
        data: Any = None,
        message: str = "",
        success: bool = True,
        status_code: int = 200,
        code: str = "ok",
    ):
        self.data = data
        self.message = message
        self.success = success
        self.status_code = status_code
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        response = {
            "success": self.success,
            "message": self.message,
        }
        if self.code:
            response["code"] = self.code
        if self.data is not None:
            response["data"] = self.data
        return response

    def to_json_response(self) -> JsonResponse:
        """转换为Django JsonResponse"""
        return JsonResponse(
            data=self.to_dict(),
            status=self.status_code,
            safe=isinstance(self.data, (dict, list)),
        )


class SuccessResponse(ApiResponse):
    """成功响应"""

    def __init__(self, data: Any = None, message: str = "操作成功", code: str = "ok"):
        super().__init__(data=data, message=message, success=True, status_code=200, code=code)


class CreatedResponse(ApiResponse):
    """创建成功响应"""

    def __init__(self, data: Any = None, message: str = "创建成功", code: str = "created"):
        super().__init__(data=data, message=message, success=True, status_code=201, code=code)


class ErrorResponse(ApiResponse):
    """通用错误响应"""

    def __init__(self, message: str = "操作失败", status_code: int = 400, data: Any = None, code: str = "error"):
        super().__init__(data=data, message=message, success=False, status_code=status_code, code=code)


class PaginatedResponse:
    """分页响应格式"""

    def __init__(self, objects_list: List[Any], page: int = 1, page_size: int = 10, total_count: Optional[int] = None):
        self.objects_list = objects_list
        self.page = page
        self.page_size = page_size
        self.total_count = total_count if total_count is not None else len(objects_list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为分页字典格式"""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "results": self.objects_list,
                "pagination": {
                    "page": self.page,
                    "page_size": self.page_size,
                    "total_count": self.total_count,
                    "total_pages": total_pages,
                    "has_next": self.page < total_pages,
                    "has_previous": self.page > 1,
                },
            },
        }

    def to_json_response(self) -> JsonResponse:
        """转换为Django JsonResponse"""
        return JsonResponse(self.to_dict())


# ==================== API 层辅助函数 ====================
# 这些函数仅供 API 层使用


def success_response(data=None, message: str = "操作成功", status_code: int = 200):
    """成功响应辅助函数（API 层使用）"""
    resp = ApiResponse(data=data, message=message, success=True, status_code=status_code, code="ok")
    return resp.to_json_response()


def error_response(message: str = "操作失败", status_code: int = 400, data=None, code: str = "error"):
    """错误响应辅助函数（API 层使用）"""
    resp = ApiResponse(data=data, message=message, success=False, status_code=status_code, code=code)
    return resp.to_json_response()
