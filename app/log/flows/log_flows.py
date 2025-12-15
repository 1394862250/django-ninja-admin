"""日志业务流程"""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from ..actions.log_actions import get_logs_queryset_action, create_log_action, delete_log_action
from ..model import Log

User = get_user_model()


def filter_logs_flow(
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
) -> QuerySet:
    """过滤日志流程"""
    queryset = get_logs_queryset_action()

    if level:
        queryset = queryset.filter(level=level)
    if category:
        queryset = queryset.filter(category=category)
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if action:
        queryset = queryset.filter(action__icontains=action)
    if start_date:
        queryset = queryset.filter(created__gte=start_date)
    if end_date:
        queryset = queryset.filter(created__lte=end_date)
    if ip_address:
        queryset = queryset.filter(ip_address__icontains=ip_address)
    if path:
        queryset = queryset.filter(path__icontains=path)
    if method:
        queryset = queryset.filter(method=method)
    if status_code:
        queryset = queryset.filter(status_code=status_code)

    return queryset


def get_log_level_flow(status_code: int) -> str:
    """根据状态码确定日志级别"""
    if status_code < 300:
        return Log.LEVEL.INFO
    elif status_code < 400:
        return Log.LEVEL.INFO
    elif status_code < 500:
        return Log.LEVEL.WARNING
    else:
        return Log.LEVEL.ERROR


def get_log_category_flow(path: str) -> str:
    """根据请求路径确定日志类别"""
    if path.startswith('/api/auth/'):
        return Log.CATEGORY.auth
    elif path.startswith('/api/user/'):
        return Log.CATEGORY.user
    elif path.startswith('/api/notification/'):
        return Log.CATEGORY.notification
    elif path.startswith('/api/'):
        return Log.CATEGORY.api
    elif path.startswith('/manage/'):
        return Log.CATEGORY.admin
    else:
        return Log.CATEGORY.system


def get_log_action_flow(method: str, path: str) -> str:
    """根据请求方法和路径确定操作动作"""
    path_parts = path.strip('/').split('/')
    if len(path_parts) >= 2:
        resource_type = path_parts[1]
    else:
        resource_type = 'unknown'
    
    if method == 'GET':
        if path.endswith('/') or len(path_parts) <= 2:
            action = f'查看{resource_type}列表'
        else:
            action = f'查看{resource_type}详情'
    elif method == 'POST':
        action = f'创建{resource_type}'
    elif method == 'PUT' or method == 'PATCH':
        action = f'更新{resource_type}'
    elif method == 'DELETE':
        action = f'删除{resource_type}'
    else:
        action = f'{method} {resource_type}'
    
    return action


def create_request_log_flow(
    user: Optional[User],
    ip_address: Optional[str],
    user_agent: str,
    path: str,
    method: str,
    status_code: int,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """创建请求日志流程"""
    level = get_log_level_flow(status_code)
    category = get_log_category_flow(path)
    action = get_log_action_flow(method, path)
    message = f"{method} {path} - {status_code}"

    try:
        create_log_action(
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
    except Exception as e:
        # 记录日志失败不应该影响正常业务流程
        print(f"创建请求日志失败: {e}")


def delete_log_flow(log_id: int) -> Tuple[bool, str]:
    """删除单个日志流程"""
    try:
        log = Log.objects.get(id=log_id)
        delete_log_action(log)
        return True, ""
    except Log.DoesNotExist:
        return False, "日志不存在"
    except Exception as e:
        return False, f"删除失败: {str(e)}"


def delete_logs_batch_flow(log_ids: List[int]) -> Tuple[int, str]:
    """批量删除日志流程"""
    if not log_ids:
        return 0, "请选择要删除的日志"

    try:
        logs = Log.objects.filter(id__in=log_ids)
        count = logs.count()
        for log in logs:
            delete_log_action(log)
        return count, ""
    except Exception as e:
        return 0, f"批量删除失败: {str(e)}"


def get_log_stats_flow() -> Dict[str, Any]:
    """获取日志统计信息流程"""
    from django.utils import timezone
    from datetime import timedelta

    level_stats = {level: Log.objects.filter(level=level).count() for level, _ in Log.LEVEL}
    category_stats = {cat: Log.objects.filter(category=cat).count() for cat, _ in Log.CATEGORY}
    recent_count = Log.objects.filter(created__gte=timezone.now() - timedelta(days=7)).count()
    today_count = Log.objects.filter(created__date=timezone.now().date()).count()
    total_count = Log.objects.count()

    return {
        "level_stats": level_stats,
        "category_stats": category_stats,
        "recent_count": recent_count,
        "today_count": today_count,
        "total_count": total_count,
    }


def list_logs_with_pagination_flow(
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
    """获取分页日志列表流程"""
    from django.core.paginator import Paginator

    # 获取过滤后的查询集
    queryset = filter_logs_flow(
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

    # 分页
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # 序列化
    items = []
    for log in page_obj:
        items.append({
            "id": log.id,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "user_id": log.user.id if log.user else None,
            "username": log.user.username if log.user else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "path": log.path,
            "method": log.method,
            "status_code": log.status_code,
            "action": log.action,
            "extra_data": log.extra_data,
            "created": log.created.isoformat() if log.created else None,
        })

    return {
        "items": items,
        "count": paginator.count,
        "page": page,
        "per_page": per_page,
        "pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }

