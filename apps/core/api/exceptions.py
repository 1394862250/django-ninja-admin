"""基础业务异常定义，便于统一拦截并格式化输出。"""


class APIException(Exception):
    """通用 API 层异常，携带状态码与错误码。"""

    status_code = 400
    code = "error"
    message = "操作失败"

    def __init__(self, message: str | None = None, status_code: int | None = None, code: str | None = None, data=None):
        msg = message or self.message
        super().__init__(msg)
        self.message = msg
        self.status_code = status_code or self.status_code
        self.code = code or self.code
        self.data = data

    def to_dict(self):
        payload = {
            "success": False,
            "message": self.message,
            "code": self.code,
        }
        if self.data is not None:
            payload["data"] = self.data
        return payload


class AuthenticationException(APIException):
    status_code = 401
    code = "authentication_failed"
    message = "未认证或认证已失效"


class PermissionException(APIException):
    status_code = 403
    code = "permission_denied"
    message = "权限不足"


class NotFoundException(APIException):
    status_code = 404
    code = "not_found"
    message = "请求的资源不存在"


class ValidationException(APIException):
    status_code = 400
    code = "validation_error"
    message = "参数校验失败"


class BusinessException(APIException):
    status_code = 400
    code = "business_error"
    message = "业务处理失败"


__all__ = [
    "APIException",
    "AuthenticationException",
    "PermissionException",
    "NotFoundException",
    "ValidationException",
    "BusinessException",
]
