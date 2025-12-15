"""日志API：使用 django-ninja-extra 自动 CRUD 并保留统计接口"""
from datetime import datetime, timedelta
from typing import List, Optional

from django.utils import timezone
from ninja import ModelSchema, Query, Schema
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    route,
)
from ninja_extra.pagination import PageNumberPaginationExtra

from .flows.log_flows import filter_logs_flow
from .model import Log


class LogOut(ModelSchema):
    """日志输出Schema"""

    class Meta:
        model = Log
        fields = "__all__"


class LogFilterSchema(Schema):
    """日志过滤条件"""

    level: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None


@api_controller("/logs", tags=["日志管理"])
class LogController(ModelControllerBase):
    """基于模型的日志控制器，自动生成CRUD并提供统计接口"""

    model_config = ModelConfig(
        model=Log,
        schema_config=ModelSchemaConfig(
            read_only_fields=["id", "created", "modified"],
        ),
        pagination_class=PageNumberPaginationExtra,
    )

    def get_queryset(self):
        """默认查询集：按创建时间倒序，预加载用户"""
        return Log.objects.select_related("user").order_by("-created")

    @route.get("", response=List[LogOut])
    def list_logs(
        self,
        filters: LogFilterSchema = Query(...),
        page: int = 1,
        page_size: int = 10,
    ):
        """带过滤与分页的列表"""
        queryset = filter_logs_flow(
            level=filters.level,
            category=filters.category,
            user_id=filters.user_id,
            action=filters.action,
            start_date=filters.start_date,
            end_date=filters.end_date,
            ip_address=filters.ip_address,
            path=filters.path,
            method=filters.method,
            status_code=filters.status_code,
        )
        paginator = PageNumberPaginationExtra(page_size)
        return paginator.paginate_queryset(queryset, self.request)

    @route.get("/stats")
    def stats(self):
        """日志统计"""
        level_stats = {level: Log.objects.filter(level=level).count() for level, _ in Log.LEVEL}
        category_stats = {cat: Log.objects.filter(category=cat).count() for cat, _ in Log.CATEGORY}
        recent_count = Log.objects.filter(created__gte=timezone.now() - timedelta(days=7)).count()
        today_count = Log.objects.filter(created__date=timezone.now().date()).count()

        return {
            "level_stats": level_stats,
            "category_stats": category_stats,
            "recent_count": recent_count,
            "today_count": today_count,
            "total_count": Log.objects.count(),
        }
