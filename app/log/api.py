"""日志API接口"""
from ninja import Router, Query
from ninja.pagination import paginate
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from typing import List, Optional

from .model import Log
from .schema import LogSchema, LogCreateSchema, LogFilterSchema

router = Router(tags=["日志管理"])

User = get_user_model()


@router.get("/logs")
def list_logs(request, filters: LogFilterSchema = Query(...), page: int = 1, per_page: int = 10):
    """
    获取日志列表，支持分页和过滤
    """
    queryset = Log.objects.all()
    
    # 应用过滤条件
    if filters.level:
        queryset = queryset.filter(level=filters.level)
    
    if filters.category:
        queryset = queryset.filter(category=filters.category)
    
    if filters.user_id:
        queryset = queryset.filter(user_id=filters.user_id)
    
    if filters.action:
        queryset = queryset.filter(action__icontains=filters.action)
    
    if filters.start_date:
        queryset = queryset.filter(created__gte=filters.start_date)
    
    if filters.end_date:
        queryset = queryset.filter(created__lte=filters.end_date)
    
    if filters.ip_address:
        queryset = queryset.filter(ip_address__icontains=filters.ip_address)
    
    if filters.path:
        queryset = queryset.filter(path__icontains=filters.path)
    
    if filters.method:
        queryset = queryset.filter(method=filters.method)
    
    if filters.status_code:
        queryset = queryset.filter(status_code=filters.status_code)
    
    # 预加载用户信息
    queryset = queryset.select_related('user').order_by('-created')
    
    # 手动实现分页
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    
    # 使用Schema序列化数据
    items = [LogSchema.from_orm(log) for log in page_obj.object_list]
    
    # 创建响应数据
    response_data = {
        "items": items,
        "count": paginator.count,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "per_page": per_page,
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return response_data


@router.get("/logs/stats")
def get_log_stats(request):
    """
    获取日志统计信息
    """
    # 按级别统计
    level_stats = {}
    for level, _ in Log.LEVEL:
        count = Log.objects.filter(level=level).count()
        level_stats[level] = count
    
    # 按类别统计
    category_stats = {}
    for category, _ in Log.CATEGORY:
        count = Log.objects.filter(category=category).count()
        category_stats[category] = count
    
    # 最近7天的日志数量
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    recent_count = Log.objects.filter(created__gte=seven_days_ago).count()
    
    # 今日日志数量
    today = timezone.now().date()
    today_count = Log.objects.filter(created__date=today).count()
    
    return {
        "level_stats": level_stats,
        "category_stats": category_stats,
        "recent_count": recent_count,
        "today_count": today_count,
        "total_count": Log.objects.count()
    }


@router.get("/logs/{log_id}", response=LogSchema)
def get_log(request, log_id: int):
    """
    获取单个日志详情
    """
    try:
        log = Log.objects.select_related('user').get(id=log_id)
        return log
    except Log.DoesNotExist:
        from ninja.errors import HttpError
        raise HttpError(404, "日志不存在")


@router.post("/logs", response=LogSchema)
def create_log(request, data: LogCreateSchema):
    """
    创建新日志
    """
    # 获取当前用户，如果未认证则为None
    user = request.user if request.user.is_authenticated else None
    
    log = Log.objects.create(
        user=user,
        level=data.level,
        category=data.category,
        action=data.action,
        message=data.message,
        ip_address=data.ip_address,
        user_agent=data.user_agent,
        path=data.path,
        method=data.method,
        status_code=data.status_code,
        extra_data=data.extra_data or {}
    )
    
    return log


@router.delete("/logs/{log_id}")
def delete_log(request, log_id: int):
    """
    删除日志
    """
    try:
        log = Log.objects.get(id=log_id)
        log.delete()
        return {"success": True, "message": "日志已删除"}
    except Log.DoesNotExist:
        from ninja.errors import HttpError
        raise HttpError(404, "日志不存在")


@router.delete("/logs/batch")
def batch_delete_logs(request, log_ids: List[int]):
    """
    批量删除日志
    """
    deleted_count, _ = Log.objects.filter(id__in=log_ids).delete()
    return {"success": True, "message": f"已删除 {deleted_count} 条日志"}


# 辅助函数：记录日志
def log_action(
    level: str,
    category: str,
    action: str,
    message: str,
    user=None,
    ip_address=None,
    user_agent=None,
    path=None,
    method=None,
    status_code=None,
    extra_data=None
):
    """
    记录系统日志的辅助函数
    
    Args:
        level: 日志级别
        category: 日志类别
        action: 操作动作
        message: 日志消息
        user: 用户对象
        ip_address: IP地址
        user_agent: 用户代理
        path: 请求路径
        method: 请求方法
        status_code: 状态码
        extra_data: 额外数据
    """
    Log.objects.create(
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
        extra_data=extra_data or {}
    )
