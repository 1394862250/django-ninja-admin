"""日志API：使用 django-ninja-extra 自动 CRUD 并保留统计接口"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Query, Schema
from ninja_extra import (
    api_controller,
    route,
    ControllerBase,
)
from apps.core.api.responses import success_response, error_response
from apps.core.api.permissions import IsStaffOrSuperuser

from .services import (
    delete_log,
    delete_logs_batch,
    get_log_stats,
    paginate_logs,
    seed_logs,
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
    log_ids: List[str]


class LogSeedSchema(Schema):
    """批量生成日志 Schema"""
    count: int = 20
    level: Optional[str] = None
    category: Optional[str] = None


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
        user_id: Optional[UUID] = Query(None),
        action: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        ip_address: Optional[str] = Query(None),
        path: Optional[str] = Query(None),
        method: Optional[str] = Query(None),
        status_code: Optional[int] = Query(None),
    ):
        """带过滤与分页的列表 - 服务层处理过滤/分页"""
        data = paginate_logs(
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
        return success_response(data=data, message="获取日志列表成功")

    @route.get("/stats")
    def stats(self):
        """日志统计"""
        return success_response(data=get_log_stats(), message="获取日志统计成功")

    @route.get("/{log_id}")
    def get_log(self, log_id: str):
        """获取单个日志详情"""
        from .services import get_log_detail
        log = get_log_detail(log_id)
        if not log:
            return error_response(message="日志不存在", status_code=404)
        return success_response(data=log, message="获取日志详情成功")

    @route.post("/seed", permissions=[IsStaffOrSuperuser])
    def seed(self, payload: LogSeedSchema):
        """批量生成测试日志"""
        result = seed_logs(self.context.request.user, count=payload.count, level=payload.level, category=payload.category)
        return success_response(message=f"已生成 {result.get('created', 0)} 条日志", data=result)

    @route.delete("/batch-delete")
    def batch_delete(self, payload: BatchDeleteSchema):
        """批量删除日志"""
        deleted_count, error_msg = delete_logs_batch(payload.log_ids)
        if error_msg:
            return error_response(message=error_msg, status_code=400)
        return success_response(message=f"成功删除 {deleted_count} 条日志")

    @route.delete("/{log_id}")
    def delete_log(self, log_id: str):
        """删除单个日志"""
        success, error_msg = delete_log(log_id)
        if not success:
            status = 404 if "不存在" in (error_msg or "") else 400
            return error_response(message=error_msg, status_code=status)
        return success_response(message="日志已删除")
