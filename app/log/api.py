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
    ControllerBase,
)
from ninja_extra.pagination import PageNumberPaginationExtra

from .flows.log_flows import (
    filter_logs_flow,
    delete_log_flow,
    delete_logs_batch_flow,
    get_log_stats_flow,
    list_logs_with_pagination_flow,
)
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


class BatchDeleteSchema(Schema):
    """批量删除Schema"""
    log_ids: List[int]


@api_controller("/logs", tags=["日志管理"])
class LogController(ControllerBase):
    """日志控制器 - 手动实现所有接口"""

    @route.get("")
    def list_logs(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        level: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
        action: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        ip_address: Optional[str] = Query(None),
        path: Optional[str] = Query(None),
        method: Optional[str] = Query(None),
        status_code: Optional[int] = Query(None),
    ):
        """带过滤与分页的列表 - 调用 Flow"""
        return list_logs_with_pagination_flow(
            page=page,
            per_page=per_page,
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

    @route.get("/stats")
    def stats(self):
        """日志统计 - 调用 Flow"""
        return get_log_stats_flow()

    @route.delete("/batch-delete")
    def batch_delete(self, payload: BatchDeleteSchema):
        """批量删除日志"""
        deleted_count, error_msg = delete_logs_batch_flow(payload.log_ids)
        if error_msg:
            return {"success": False, "message": error_msg}
        return {"success": True, "message": f"成功删除 {deleted_count} 条日志"}

    @route.delete("/{log_id}")
    def delete_log(self, log_id: int):
        """删除单个日志"""
        success, error_msg = delete_log_flow(log_id)
        if not success:
            return {"success": False, "message": error_msg}
        return {"success": True, "message": "日志已删除"}

