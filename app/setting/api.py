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
from ninja import File, Schema, ModelSchema
from ninja.files import UploadedFile
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    route,
)
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
    value_type: Literal["boolean", "integer", "float", "string", "text", "json", "url", "email"]
    category: Literal["system", "feature", "ui", "email", "security", "notification", "api", "business"]
    value: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_editable: bool = True
    sort_order: int = 0
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    extra_options: Dict[str, Any] = Field(default_factory=dict)


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


class SystemSettingOut(ModelSchema):
    """设置输出Schema"""
    class Meta:
        model = SystemSetting
        fields = [
            "id",
            "key",
            "name",
            "value_type",
            "category",
            "value",
            "default_value",
            "description",
            "is_active",
            "is_editable",
            "sort_order",
            "validation_rules",
            "extra_options",
            "created",
            "modified",
        ]


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


@api_controller("/settings", tags=["系统设置"])
class SettingController(ModelControllerBase):
    """系统设置控制器 - 重构版"""
    model_config = ModelConfig(
        model=SystemSetting,
        schema_config=ModelSchemaConfig(
            read_only_fields=["id", "created", "modified"],
        ),
    )

    def get_queryset(self):
        """默认查询：按分类、排序"""
        from .flows.setting_flows import get_settings_queryset_flow
        return get_settings_queryset_flow()

    def create(self, payload: SystemSettingCreate):
        """创建设置 - Flow 内部处理权限判断"""
        user = self.request.user
        success, error_msg, setting = create_setting_flow(user, payload.dict())
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置创建成功")

    def update(self, id: int, payload: SystemSettingUpdate):
        """更新设置 - Flow 内部处理权限判断"""
        user = self.request.user
        # 过滤掉 None 值
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        success, error_msg, setting = update_setting_flow(user, id, update_data)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置更新成功")

    def partial_update(self, id: int, payload: SystemSettingUpdate):
        """部分更新设置 - Flow 内部处理权限判断"""
        return self.update(id, payload)

    def delete(self, id: int):
        """删除设置 - Flow 内部处理权限判断"""
        user = self.request.user
        success, error_msg = delete_setting_flow(user, id)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置已删除")

    @route.get("/grouped", response=Dict[str, Any])
    def get_settings_grouped(self):
        """获取按分类分组的设置"""
        result = get_settings_grouped_flow()
        return success_response(data=result)

    @route.get("/by-key/{key}", response=SystemSettingOut)
    def get_setting(self, key: str):
        """根据键名获取设置"""
        from .flows.setting_flows import get_setting_by_key_flow
        try:
            setting = get_setting_by_key_flow(key)
            return setting
        except SystemSetting.DoesNotExist:
            from django.http import Http404
            raise Http404("设置不存在")

    @route.get("/value/{key}", response=SettingValueOut)
    def get_setting_value(self, key: str):
        """获取设置值"""
        success, error_msg, data = get_setting_value_flow(key)
        if not success:
            return error_response(error_msg, status_code=404)
        return data

    @route.put("/value/{key}", response=SettingValueOut)
    def update_setting_value(self, key: str, data: SystemSettingValueUpdate):
        """更新设置值 - Flow 内部处理权限判断"""
        user = self.request.user
        success, error_msg, result = update_setting_value_flow(user, key, data.value, data.validate)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return result

    @route.post("/batch-update", response=Dict[str, Any])
    def batch_update_settings(self, payload: BatchUpdateSettings):
        """批量更新设置 - Flow 内部处理权限判断"""
        user = self.request.user
        settings_data = [{"key": item.key, "value": item.value, "validate": item.validate} for item in payload.settings]
        success, error_msg, result = batch_update_settings_flow(user, settings_data)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(data=result)

    @route.delete("/by-key/{key}")
    def delete_setting(self, key: str):
        """根据键名删除设置 - Flow 内部处理权限判断"""
        user = self.request.user
        success, error_msg = delete_setting_by_key_flow(user, key)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="设置已删除")

    @route.post("/validate/{key}", response=SettingValidationResult)
    def validate_setting_value(self, key: str, value: str):
        """验证设置值"""
        success, valid, message = validate_setting_value_flow(key, value)
        if not success:
            return {"valid": False, "message": message}
        return {"valid": valid, "message": message}

    @route.get("/dictionary", response=Dict[str, Any])
    def get_settings_dictionary(self):
        """获取设置字典"""
        result = get_settings_dictionary_flow()
        return success_response(data={"settings": result, "count": len(result)})

    @route.post("/reset-defaults", response=Dict[str, Any])
    def reset_settings_to_defaults(self):
        """重置设置为默认值 - Flow 内部处理权限判断"""
        user = self.request.user
        success, error_msg, reset_count = reset_settings_to_defaults_flow(user)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message=f"已重置 {reset_count} 项设置", data={"reset_count": reset_count})

    @route.post("/upload", response=Dict[str, Any])
    def upload_setting_asset(self, file: UploadedFile = File(...)):
        """上传设置资源文件 - Flow 内部处理权限判断"""
        user = self.request.user
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
