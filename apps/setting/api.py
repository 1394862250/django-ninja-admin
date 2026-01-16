"""设置管理 API（扁平化分层版本）。"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from ninja import File, Query, Router
from ninja.files import UploadedFile

from apps.core.api.exceptions import NotFoundException
from apps.core.api.responses import success_response
from .model import SystemSetting
from .schemas import (
    BatchUpdateSettingsSchema,
    SettingCreateSchema,
    SettingUpdateSchema,
    SettingValidationResultSchema,
    SettingValueUpdateSchema,
)
from .selectors import get_setting_by_id, get_setting_by_key, paginate_settings, serialize_setting
from .services import (
    batch_update_settings,
    create_setting,
    delete_setting,
    delete_setting_by_key,
    get_setting_value_detail,
    get_settings_dictionary,
    get_settings_grouped,
    reset_settings_to_defaults,
    set_setting_value,
    update_setting,
    upload_setting_asset,
    validate_setting_value,
)


def create_setting_api_router():
    """创建设置 API 路由。"""
    router = Router(tags=["系统设置"])

    @router.get("/settings/list")
    def list_settings(
        request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        active_only: bool = Query(False),
        category: Optional[str] = Query(None),
    ):
        data = paginate_settings(page, page_size, active_only=active_only, category=category)
        return success_response(data=data)

    @router.get("/settings/{setting_id}")
    def get_setting_detail(request, setting_id: UUID):
        try:
            setting = get_setting_by_id(setting_id)
        except SystemSetting.DoesNotExist:
            raise NotFoundException("设置不存在")
        return success_response(data=serialize_setting(setting, typed_value=True))

    @router.post("/settings")
    def create(request, payload: SettingCreateSchema):
        setting = create_setting(request.user, payload.dict())
        return success_response(data=serialize_setting(setting, typed_value=True), message="设置创建成功", status_code=201)

    @router.put("/settings/{setting_id}")
    def update(request, setting_id: UUID, payload: SettingUpdateSchema):
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        setting = update_setting(request.user, setting_id, update_data)
        return success_response(data=serialize_setting(setting, typed_value=True), message="设置更新成功")

    @router.patch("/settings/{setting_id}")
    def partial_update(request, setting_id: UUID, payload: SettingUpdateSchema):
        return update(request, setting_id, payload)

    @router.delete("/settings/{setting_id}")
    def delete_setting_api(request, setting_id: UUID):
        delete_setting(request.user, setting_id)
        return success_response(message="设置已删除")

    @router.get("/settings/grouped")
    def grouped_settings(request):
        return success_response(data=get_settings_grouped())

    @router.get("/settings/by-key/{key}")
    def get_setting_by_key_api(request, key: str):
        try:
            setting = get_setting_by_key(key)
        except SystemSetting.DoesNotExist:
            raise NotFoundException("设置不存在")
        return success_response(data=serialize_setting(setting, typed_value=True))

    @router.get("/settings/value/{key}")
    def get_setting_value_api(request, key: str):
        return success_response(data=get_setting_value_detail(key))

    @router.put("/settings/value/{key}")
    def update_setting_value_api(request, key: str, payload: SettingValueUpdateSchema):
        updated = set_setting_value(request.user, key, payload.value, validate=payload.validate)
        return success_response(data=updated, message="设置值已更新")

    @router.post("/settings/batch-update")
    def batch_update_settings_api(request, payload: BatchUpdateSettingsSchema):
        summary = batch_update_settings(request.user, [item.dict() for item in payload.settings])
        return success_response(data=summary)

    @router.delete("/settings/by-key/{key}")
    def delete_setting_by_key_api(request, key: str):
        delete_setting_by_key(request.user, key)
        return success_response(message="设置已删除")

    @router.post("/settings/validate/{key}", response=SettingValidationResultSchema)
    def validate_setting_value_api(request, key: str, value: str):
        valid, message = validate_setting_value(key, value)
        return {"valid": valid, "message": message}

    @router.get("/settings/dictionary")
    def settings_dictionary_api(request):
        settings = get_settings_dictionary()
        return success_response(data={"settings": settings, "count": len(settings)})

    @router.post("/settings/reset-defaults")
    def reset_settings_api(request):
        reset_count = reset_settings_to_defaults(request.user)
        return success_response(message=f"已重置 {reset_count} 项设置", data={"reset_count": reset_count})

    @router.post("/settings/upload")
    def upload_setting_asset_api(request, file: UploadedFile = File(...)):
        upload_result = upload_setting_asset(request.user, file=file)
        return success_response(message="上传成功", data=upload_result)

    return router
