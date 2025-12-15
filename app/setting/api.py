"""设置管理API - 重构版
符合架构约束：
1. API 层只负责参数解析与返回
2. 权限判断在 Flow 中
3. 业务逻辑在 Flow/Action 中
"""
import os
from uuid import uuid4
from typing import Dict, Any, Optional, List, Literal
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from ninja import File, Schema, ModelSchema, Query, Router
from ninja.files import UploadedFile
from pydantic import Field

from .models import SystemSetting
from .flows.setting_flows import (
    get_settings_grouped_flow,
    get_setting_value_flow,
    update_setting_value_flow,
    batch_update_settings_flow,
    delete_setting_by_key_flow,
    validate_setting_value_flow,
    get_settings_dictionary_flow,
    reset_settings_to_defaults_flow,
    create_setting_flow,
    update_setting_flow,
    delete_setting_flow,
    can_manage_settings_flow,
    get_settings_queryset_flow,
    get_setting_by_key_flow,
)
from app.utils.responses import ApiResponse


def success_response(data=None, message="操作成功", status_code=200):
    return ApiResponse(data=data, message=message, success=True, status_code=status_code).to_json_response()


def error_response(message="操作失败", status_code=400, data=None):
    return ApiResponse(data=data, message=message, success=False, status_code=status_code).to_json_response()


# Schema 定义
class SystemSettingBase(Schema):
    """设置基础Schema"""
    key: str
    name: str
    value_type: str
    category: str
    value: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_editable: bool = True
    sort_order: int = 0
    validation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extra_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SystemSettingCreate(SystemSettingBase):
    """创建设置Schema"""
    pass


class SystemSettingUpdate(Schema):
    """更新设置Schema"""
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    extra_options: Optional[Dict[str, Any]] = None


class SystemSettingOut(SystemSettingBase):
    """设置输出Schema"""
    id: int
    created: str
    modified: str

    class Config:
        from_attributes = True


class SystemSettingValueUpdate(Schema):
    """更新设置值Schema"""
    key: str = Field(..., description="设置键名")
    value: str = Field(..., description="设置值")
    validate: bool = Field(default=True, description="是否验证值")


class BatchUpdateSettings(Schema):
    """批量更新设置Schema"""
    settings: List[SystemSettingValueUpdate]


class SettingValidationResult(Schema):
    """设置验证结果Schema"""
    valid: bool
    message: str


class SettingValueOut(Schema):
    """设置值输出Schema"""
    key: str
    name: str
    value: Any
    value_type: str
    description: Optional[str] = None


def create_setting_api_router():
    """创建设置API路由"""
    router = Router(tags=["系统设置"])

    @router.get("/settings/list")
    def list_settings(
        request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        active_only: bool = Query(False),
        category: Optional[str] = Query(None),
    ):
        """获取设置列表 - 手动实现分页和序列化"""
        from django.core.paginator import Paginator

        queryset = get_settings_queryset_flow()

        # 过滤
        if active_only:
            queryset = queryset.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)

        # 分页
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # 手动序列化
        items = []
        for setting in page_obj:
            items.append({
                "id": setting.id,
                "key": setting.key,
                "name": setting.name,
                "value_type": setting.value_type,
                "category": setting.category,
                "value": setting.value,
                "default_value": setting.default_value,
                "description": setting.description,
                "is_active": setting.is_active,
                "is_editable": setting.is_editable,
                "sort_order": setting.sort_order,
                "validation_rules": setting.validation_rules or {},
                "extra_options": setting.extra_options or {},
                "created": setting.created.isoformat() if setting.created else None,
                "modified": setting.modified.isoformat() if setting.modified else None,
            })

        return success_response(data={
            "results": items,
            "count": paginator.count,
            "page": page,
            "page_size": page_size,
            "pages": paginator.num_pages,
        })

    @router.get("/settings/{id}")
    def get_setting(request, id: int):
        """获取单个设置详情"""
        try:
            setting = SystemSetting.objects.get(id=id)
            return success_response(data={
                "id": setting.id,
                "key": setting.key,
                "name": setting.name,
                "value_type": setting.value_type,
                "category": setting.category,
                "value": setting.value,
                "default_value": setting.default_value,
                "description": setting.description,
                "is_active": setting.is_active,
                "is_editable": setting.is_editable,
                "sort_order": setting.sort_order,
                "validation_rules": setting.validation_rules or {},
                "extra_options": setting.extra_options or {},
                "created": setting.created.isoformat() if setting.created else None,
                "modified": setting.modified.isoformat() if setting.modified else None,
            })
        except SystemSetting.DoesNotExist:
            return error_response(message="设置不存在", status_code=404)

    @router.post("/settings")
    def create(request, payload: SystemSettingCreate):
        """创建设置 - Flow 内部处理权限判断"""
        user = request.user
        success, error_msg, setting = create_setting_flow(user, payload.dict())
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置创建成功")

    @router.put("/settings/{id}")
    def update(request, id: int, payload: SystemSettingUpdate):
        """更新设置 - Flow 内部处理权限判断"""
        user = request.user
        # 过滤掉 None 值
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        success, error_msg, setting = update_setting_flow(user, id, update_data)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置更新成功")

    @router.patch("/settings/{id}")
    def partial_update(request, id: int, payload: SystemSettingUpdate):
        """部分更新设置 - Flow 内部处理权限判断"""
        return update(request, id, payload)

    @router.delete("/settings/{id}")
    def delete_setting(request, id: int):
        """删除设置 - Flow 内部处理权限判断"""
        user = request.user
        success, error_msg = delete_setting_flow(user, id)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置已删除")

    @router.get("/settings/grouped", response=Dict[str, Any])
    def get_settings_grouped(request):
        """获取按分类分组的设置"""
        result = get_settings_grouped_flow()
        return success_response(data=result)

    @router.get("/settings/by-key/{key}")
    def get_setting_by_key(request, key: str):
        """根据键名获取设置 - Flow 内部处理异常"""
        success, error_msg, setting = get_setting_by_key_flow(key)
        if not success:
            return error_response(error_msg, status_code=404)

        return success_response(data={
            "id": setting.id,
            "key": setting.key,
            "name": setting.name,
            "value_type": setting.value_type,
            "category": setting.category,
            "value": setting.value,
            "default_value": setting.default_value,
            "description": setting.description,
            "is_active": setting.is_active,
            "is_editable": setting.is_editable,
            "sort_order": setting.sort_order,
            "validation_rules": setting.validation_rules or {},
            "extra_options": setting.extra_options or {},
            "created": setting.created.isoformat() if setting.created else None,
            "modified": setting.modified.isoformat() if setting.modified else None,
        })

    @router.get("/settings/value/{key}", response=SettingValueOut)
    def get_setting_value(request, key: str):
        """获取设置值"""
        success, error_msg, data = get_setting_value_flow(key)
        if not success:
            return error_response(error_msg, status_code=404)
        return data

    @router.put("/settings/value/{key}", response=SettingValueOut)
    def update_setting_value(request, key: str, data: SystemSettingValueUpdate):
        """更新设置值 - Flow 内部处理权限判断"""
        user = request.user
        success, error_msg, result = update_setting_value_flow(user, key, data.value, data.validate)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return result

    @router.post("/settings/batch-update", response=Dict[str, Any])
    def batch_update_settings(request, payload: BatchUpdateSettings):
        """批量更新设置 - Flow 内部处理权限判断"""
        user = request.user
        settings_data = [{"key": item.key, "value": item.value, "validate": item.validate} for item in payload.settings]
        success, error_msg, result = batch_update_settings_flow(user, settings_data)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(data=result)

    @router.delete("/settings/by-key/{key}")
    def delete_setting_by_key(request, key: str):
        """根据键名删除设置 - Flow 内部处理权限判断"""
        user = request.user
        success, error_msg = delete_setting_by_key_flow(user, key)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置已删除")

    @router.post("/settings/validate/{key}", response=SettingValidationResult)
    def validate_setting_value(request, key: str, value: str):
        """验证设置值"""
        success, valid, message = validate_setting_value_flow(key, value)
        if not success:
            return {"valid": False, "message": message}
        return {"valid": valid, "message": message}

    @router.get("/settings/dictionary", response=Dict[str, Any])
    def get_settings_dictionary(request):
        """获取设置字典"""
        result = get_settings_dictionary_flow()
        return success_response(data={"settings": result, "count": len(result)})

    @router.post("/settings/reset-defaults", response=Dict[str, Any])
    def reset_settings_to_defaults(request):
        """重置设置为默认值 - Flow 内部处理权限判断"""
        user = request.user
        success, error_msg, reset_count = reset_settings_to_defaults_flow(user)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message=f"已重置 {reset_count} 项设置", data={"reset_count": reset_count})

    @router.post("/settings/upload", response=Dict[str, Any])
    def upload_setting_asset(request, file: UploadedFile = File(...)):
        """上传设置资源文件 - Flow 内部处理权限判断"""
        user = request.user
        can_manage, error_msg = can_manage_settings_flow(user)
        if not can_manage:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)

        if not file.content_type.startswith(("image/", "video/", "application/")):
            return error_response(message="不支持的文件类型", status_code=400)

        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            return error_response(message="文件大小不能超过 5MB", status_code=400)

        extension = os.path.splitext(file.name)[1] or ""
        filename = f"settings/{uuid4().hex}{extension}"
        saved_path = default_storage.save(filename, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)

        return success_response(
            message="上传成功",
            data={
                "url": file_url,
                "path": saved_path,
                "size": file.size,
                "content_type": file.content_type,
            },
        )

    return router
