"""日志业务服务层（Services），去除 Flow/Action 过度分层。"""
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID
import random
from faker import Faker

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.utils import timezone
from apps.core.utils.request import get_client_ip
from apps.core.utils.serializers import to_iso
from apps.core.api.permissions import ensure_staff_or_superuser
from apps.core.api.exceptions import ValidationException

from .model import Log
from .selectors import base_logs_queryset

User = get_user_model()
faker = Faker("zh_CN")


def _normalize_extra_data(value: Any) -> Any:
    """将日志附加数据转换为可 JSON 序列化的结构。"""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [_normalize_extra_data(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _normalize_extra_data(v) for k, v in value.items()}
    return value


def filter_logs(
    level: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ip_address: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
) -> QuerySet:
    """基于筛选条件返回日志查询集。"""
    queryset = base_logs_queryset()

    if level:
        queryset = queryset.filter(level=level)
    if category:
        queryset = queryset.filter(category=category)
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if action:
        queryset = queryset.filter(action__icontains=action)
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    if ip_address:
        queryset = queryset.filter(ip_address__icontains=ip_address)
    if path:
        queryset = queryset.filter(path__icontains=path)
    if method:
        queryset = queryset.filter(method=method)
    if status_code:
        queryset = queryset.filter(status_code=status_code)

    return queryset


def resolve_log_level(status_code: int) -> str:
    """根据状态码确定日志级别。"""
    if status_code < 300:
        return Log.LEVEL.INFO
    elif status_code < 400:
        return Log.LEVEL.INFO
    elif status_code < 500:
        return Log.LEVEL.WARNING
    return Log.LEVEL.ERROR


def resolve_log_category(path: str) -> str:
    """根据路径确定日志类别。"""
    if path.startswith("/api/auth/"):
        return Log.CATEGORY.auth
    if path.startswith("/api/user/"):
        return Log.CATEGORY.user
    if path.startswith("/api/notification/"):
        return Log.CATEGORY.notification
    if path.startswith("/api/"):
        return Log.CATEGORY.api
    if path.startswith("/manage/"):
        return Log.CATEGORY.admin
    return Log.CATEGORY.system


def resolve_log_action(method: str, path: str) -> str:
    """根据方法/路径生成操作动作。"""
    path_parts = path.strip("/").split("/")
    resource_type = path_parts[1] if len(path_parts) >= 2 else "unknown"

    if method == "GET":
        if path.endswith("/") or len(path_parts) <= 2:
            return f"查看{resource_type}列表"
        return f"查看{resource_type}详情"
    if method == "POST":
        return f"创建{resource_type}"
    if method in ("PUT", "PATCH"):
        return f"更新{resource_type}"
    if method == "DELETE":
        return f"删除{resource_type}"
    return f"{method} {resource_type}"


def create_log_entry(
    *,
    level: str = Log.LEVEL.INFO,
    category: str = Log.CATEGORY.system,
    action: str = "unknown",
    message: str = "",
    user: Optional[User] = None,
    ip_address: Optional[str] = None,
    user_agent: str = "",
    path: str = "",
    method: str = "",
    status_code: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> Log:
    """创建日志记录。"""
    normalized_extra = _normalize_extra_data(extra_data or {})
    return Log.objects.create(
        user=user,
        level=level,
        category=category,
        action=action,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
        path=path,
        method=method,
        status_code=status_code,
        extra_data=normalized_extra,
    )


def create_request_log(
    *,
    user: Optional[User],
    ip_address: Optional[str],
    user_agent: str,
    path: str,
    method: str,
    status_code: int,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """记录请求日志（异常不影响主流程）。"""
    level = resolve_log_level(status_code)
    category = resolve_log_category(path)
    action = resolve_log_action(method, path)
    message = f"{method} {path} - {status_code}"

    try:
        create_log_entry(
            level=level,
            category=category,
            action=action,
            message=message,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            method=method,
            status_code=status_code,
            extra_data=extra_data,
        )
    except Exception as exc:
        # 记录日志失败不应该影响正常业务流程
        print(f"创建请求日志失败: {exc}")


# 便捷写日志函数（替代原 actions 层）
def create_log(
    *,
    level: str = Log.LEVEL.INFO,
    category: str = Log.CATEGORY.system,
    action: str | None = None,
    message: str | None = None,
    user: Optional[User] = None,
    request=None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """创建日志记录（便捷封装）。"""
    if request:
        ip_address = ip_address or get_client_ip(request)
        user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")
        path = path or request.path
        method = method or request.method
        user = user or (request.user if hasattr(request, "user") and getattr(request.user, "is_authenticated", False) else None)

    create_log_entry(
        level=level,
        category=category,
        action=action or "unknown",
        message=message or "",
        user=user,
        ip_address=ip_address or "",
        user_agent=user_agent or "",
        path=path or "",
        method=method or "",
        status_code=status_code,
        extra_data=extra_data or {},
    )


def log_user_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    create_log(level=level, category=Log.CATEGORY.user, action=action, message=message, user=user, request=request, extra_data=extra_data)


def log_auth_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    create_log(level=level, category=Log.CATEGORY.auth, action=action, message=message, user=user, request=request, extra_data=extra_data)


def log_system_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    create_log(level=level, category=Log.CATEGORY.system, action=action, message=message, user=user, request=request, extra_data=extra_data)


def log_api_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, status_code=None, extra_data=None):
    create_log(
        level=level,
        category=Log.CATEGORY.api,
        action=action,
        message=message,
        user=user,
        request=request,
        status_code=status_code,
        extra_data=extra_data,
    )


def log_admin_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    create_log(level=level, category=Log.CATEGORY.admin, action=action, message=message, user=user, request=request, extra_data=extra_data)


def log_notification_action(action, message, level: str = Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    create_log(level=level, category=Log.CATEGORY.notification, action=action, message=message, user=user, request=request, extra_data=extra_data)


def delete_log(log_id: str) -> Tuple[bool, str]:
    """删除单个日志。"""
    try:
        log = Log.objects.get(id=log_id)
        log.delete()
        return True, ""
    except Log.DoesNotExist:
        return False, "日志不存在"
    except Exception as exc:
        return False, f"删除失败: {exc}"


def get_log_detail(log_id: str) -> Optional[Dict[str, Any]]:
    """获取单个日志详情。"""
    try:
        log = Log.objects.select_related("user").get(id=log_id)
        return {
            "id": str(log.id),
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "user_id": str(log.user.id) if log.user else None,
            "user_username": log.user.username if log.user else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "path": log.path,
            "method": log.method,
            "status_code": log.status_code,
            "action": log.action,
            "extra_data": log.extra_data,
            "created": to_iso(log.created_at),
        }
    except Log.DoesNotExist:
        return None


def delete_logs_batch(log_ids: List[str]) -> Tuple[int, str]:
    """批量删除日志。"""
    if not log_ids:
        return 0, "请选择要删除的日志"

    try:
        logs = Log.objects.filter(id__in=log_ids)
        count = logs.count()
        logs.delete()
        return count, ""
    except Exception as exc:
        return 0, f"批量删除失败: {exc}"


def get_log_stats() -> Dict[str, Any]:
    """获取日志统计信息。"""
    level_stats = {level: Log.objects.filter(level=level).count() for level, _ in Log.LEVEL}
    category_stats = {cat: Log.objects.filter(category=cat).count() for cat, _ in Log.CATEGORY}
    recent_count = Log.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
    today_count = Log.objects.filter(created_at__date=timezone.now().date()).count()
    total_count = Log.objects.count()

    return {
        "level_stats": level_stats,
        "category_stats": category_stats,
        "recent_count": recent_count,
        "today_count": today_count,
        "total_count": total_count,
    }


def paginate_logs(
    *,
    page: int,
    per_page: int,
    level: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ip_address: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    """分页获取日志列表。"""
    queryset = filter_logs(
        level=level,
        category=category,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        path=path,
        method=method,
        status_code=status_code,
    )

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    items = [
        {
            "id": str(log.id),
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "user_id": str(log.user.id) if log.user else None,
            "username": log.user.username if log.user else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "path": log.path,
            "method": log.method,
            "status_code": log.status_code,
            "action": log.action,
            "extra_data": log.extra_data,
            "created": to_iso(log.created_at),
        }
        for log in page_obj
    ]

    return {
        "items": items,
        "count": paginator.count,
        "page": page,
        "per_page": per_page,
        "pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }


def seed_logs(
    operator: Optional[User],
    *,
    count: int = 20,
    level: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """批量生成日志（仅 staff/superuser）。"""
    ensure_staff_or_superuser(operator)

    if count < 1 or count > 50:
        raise ValidationException("单次生成数量需在 1~50 之间")

    level_choices = [lvl for lvl, _ in Log.LEVEL]
    category_choices = [cat for cat, _ in Log.CATEGORY]

    logs: List[Log] = []
    for _ in range(count):
        logs.append(
            Log(
                level=level if level else random.choice(level_choices),
                category=category if category else random.choice(category_choices),
                action=faker.word(),
                message=faker.sentence(nb_words=12),
                user=operator if operator and operator.is_authenticated else None,
                ip_address=faker.ipv4_public(),
                user_agent=faker.user_agent(),
                path=f"/api/{faker.word()}/{faker.random_int(min=1, max=999)}",
                method=random.choice(["GET", "POST", "PUT", "DELETE"]),
                status_code=random.choice([200, 201, 400, 401, 403, 404, 500]),
                extra_data={"trace_id": faker.uuid4(), "seed": True},
            )
        )

    Log.objects.bulk_create(logs)
    return {"created": len(logs), "level": level, "category": category}


__all__ = [
    "create_log_entry",
    "create_request_log",
    "delete_log",
    "delete_logs_batch",
    "filter_logs",
    "get_log_stats",
    "paginate_logs",
    "resolve_log_action",
    "resolve_log_category",
    "resolve_log_level",
    "seed_logs",
]
