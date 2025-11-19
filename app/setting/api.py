"""设置管理API"""
from typing import Dict, Any, Optional
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from app.setting.models import SystemSetting
from app.setting.schema import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingOut,
    SystemSettingValueUpdate,
    BatchUpdateSettings,
    SystemSettingGroup,
    SettingValidationResult,
    SettingValueOut,
)
from app.user.api.base import success_response, error_response


router = Router(tags=['系统设置'])


@router.get('/settings', response=Dict[str, Any])
def list_settings(
    request,
    category: Optional[str] = Query(None, description='分类过滤'),
    active_only: bool = Query(True, description='只显示激活的设置'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(20, ge=1, le=100, description='每页数量'),
):
    """获取设置列表（支持分页）"""
    queryset = SystemSetting.objects.all()

    if category:
        queryset = queryset.filter(category=category)

    if active_only:
        queryset = queryset.filter(is_active=True)

    total = queryset.count()
    settings = list(queryset.order_by('category', 'sort_order', 'key')[
                   (page - 1) * page_size:page * page_size])

    def serialize_setting(setting: SystemSetting) -> Dict[str, Any]:
        return {
            'id': setting.id,
            'key': setting.key,
            'name': setting.name,
            'value_type': setting.value_type,
            'category': setting.category,
            'value': setting.value,
            'default_value': setting.default_value,
            'description': setting.description,
            'is_active': setting.is_active,
            'is_editable': setting.is_editable,
            'sort_order': setting.sort_order,
            'validation_rules': setting.validation_rules,
            'extra_options': setting.extra_options,
            'created': setting.created.isoformat() if setting.created else None,
            'modified': setting.modified.isoformat() if setting.modified else None,
        }

    return success_response(
        data={
            'settings': [serialize_setting(setting) for setting in settings],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        }
    )


@router.get('/settings/grouped', response=Dict[str, Any])
def get_settings_grouped(request):
    """按分类获取分组的设置列表"""
    from collections import defaultdict

    settings = SystemSetting.objects.filter(is_active=True).order_by(
        'category', 'sort_order', 'key'
    )

    # 按分类分组
    grouped = defaultdict(list)
    for setting in settings:
        grouped[setting.category].append(setting)

    # 转换为响应格式
    result = []
    category_names = dict(SystemSetting.CATEGORY)

    for category, category_settings in sorted(grouped.items()):
        result.append({
            'category': category,
            'category_name': category_names.get(category, category),
            'settings': category_settings,
        })

    return success_response(data=result)


@router.get('/setting/{key}', response=SystemSettingOut)
def get_setting(request, key: str):
    """获取单个设置"""
    setting = get_object_or_404(SystemSetting, key=key, is_active=True)
    return setting


@router.get('/setting/{key}/value', response=SettingValueOut)
def get_setting_value(request, key: str):
    """获取设置值（已转换类型）"""
    setting = get_object_or_404(SystemSetting, key=key, is_active=True)
    return {
        'key': setting.key,
        'name': setting.name,
        'value': setting.get_value(),
        'value_type': setting.value_type,
        'description': setting.description,
    }


@router.post('/settings', response=SystemSettingOut)
def create_setting(request, data: SystemSettingCreate):
    """创建设置"""
    setting = SystemSetting.objects.create(**data.dict())
    return setting


@router.put('/setting/{key}', response=SystemSettingOut)
def update_setting(request, key: str, data: SystemSettingUpdate):
    """更新设置"""
    setting = get_object_or_404(SystemSetting, key=key)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(setting, attr, value)
    setting.save()
    return setting


@router.put('/setting/{key}/value', response=SettingValueOut)
def update_setting_value(request, key: str, data: SystemSettingValueUpdate):
    """更新设置值"""
    setting = get_object_or_404(SystemSetting, key=key, is_active=True)

    # 验证值
    if data.validate:
        valid, message = setting.validate_value(data.value)
        if not valid:
            return error_response(message=message, status_code=400)

    setting.set_value(data.value)
    setting.save()

    return {
        'key': setting.key,
        'name': setting.name,
        'value': setting.get_value(),
        'value_type': setting.value_type,
        'description': setting.description,
    }


@router.post('/settings/batch-update', response=Dict[str, Any])
def batch_update_settings(request, data: BatchUpdateSettings):
    """批量更新设置值"""
    updated = []
    errors = []

    for item in data.settings:
        try:
            setting = get_object_or_404(
                SystemSetting, key=item.key, is_active=True
            )

            # 验证值
            if item.validate:
                valid, message = setting.validate_value(item.value)
                if not valid:
                    errors.append({
                        'key': item.key,
                        'message': message
                    })
                    continue

            setting.set_value(item.value)
            setting.save()

            updated.append({
                'key': setting.key,
                'name': setting.name,
                'value': setting.get_value(),
            })
        except Exception as e:
            errors.append({
                'key': item.key,
                'message': str(e)
            })

    return success_response(
        data={
            'updated': updated,
            'errors': errors,
            'updated_count': len(updated),
            'error_count': len(errors),
        }
    )


@router.delete('/setting/{key}')
def delete_setting(request, key: str):
    """删除设置"""
    setting = get_object_or_404(SystemSetting, key=key)
    setting.delete()
    return success_response(message='设置已删除')


@router.post('/setting/{key}/validate', response=SettingValidationResult)
def validate_setting_value(request, key: str, value: str):
    """验证设置值"""
    setting = get_object_or_404(SystemSetting, key=key, is_active=True)
    valid, message = setting.validate_value(value)
    return {
        'valid': valid,
        'message': message,
    }


@router.get('/settings/dictionary', response=Dict[str, Any])
def get_settings_dictionary(request):
    """获取所有设置作为字典（用于前端快速访问）"""
    settings = SystemSetting.objects.filter(is_active=True)

    result = {}
    for setting in settings:
        # 如果值不为空，使用值，否则使用默认值
        result[setting.key] = setting.get_value()

    return success_response(data={
        'settings': result,
        'count': len(result),
    })


@router.post('/settings/reset-defaults', response=Dict[str, Any])
def reset_settings_to_defaults(request):
    """将所有设置重置为默认值"""
    settings = SystemSetting.objects.filter(is_active=True)
    reset_count = 0

    for setting in settings:
        if setting.default_value is not None:
            setting.value = setting.default_value
            setting.save()
            reset_count += 1

    return success_response(
        message=f'已重置 {reset_count} 项设置',
        data={'reset_count': reset_count}
    )
