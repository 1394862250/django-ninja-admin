"""系统设置模型定义。"""
from __future__ import annotations

import json
from typing import Any, Tuple

from django.db import models
from model_utils import Choices

from apps.core.models import BaseModel


class SystemSetting(BaseModel):
    """系统设置模型。"""

    VALUE_TYPE = Choices(
        ("boolean", "布尔值"),
        ("integer", "整数"),
        ("float", "浮点数"),
        ("string", "字符串"),
        ("text", "长文本"),
        ("json", "JSON数据"),
        ("url", "URL地址"),
        ("email", "邮箱地址"),
    )

    CATEGORY = Choices(
        ("system", "系统配置"),
        ("feature", "功能开关"),
        ("ui", "界面配置"),
        ("email", "邮件配置"),
        ("security", "安全配置"),
        ("notification", "通知配置"),
        ("api", "API配置"),
        ("business", "业务配置"),
    )

    key = models.CharField(
        "设置键名",
        max_length=100,
        unique=True,
        help_text="设置的唯一标识符，使用点分命名法，如：system.site_name",
    )
    name = models.CharField("设置名称", max_length=200, help_text="设置的显示名称")
    value_type = models.CharField(
        "值类型",
        max_length=20,
        choices=VALUE_TYPE,
        default=VALUE_TYPE.string,
        help_text="设置值的数据类型",
    )
    category = models.CharField(
        "分类",
        max_length=20,
        choices=CATEGORY,
        default=CATEGORY.system,
        help_text="设置的分类",
    )
    value = models.TextField("设置值", blank=True, null=True, help_text="设置的实际值")
    default_value = models.TextField("默认值", blank=True, null=True, help_text="设置的默认值")
    description = models.TextField("描述", blank=True, null=True, help_text="设置的详细说明")
    is_active = models.BooleanField("是否启用", default=True, help_text="是否启用此设置项")
    is_editable = models.BooleanField("是否可编辑", default=True, help_text="是否允许通过界面编辑")
    sort_order = models.IntegerField(
        "排序",
        default=0,
        help_text="设置项在界面中的显示顺序，数值越小越靠前",
    )
    validation_rules = models.JSONField(
        "验证规则",
        default=dict,
        blank=True,
        help_text='设置的验证规则，如：{"min": 0, "max": 100, "required": true}',
    )
    extra_options = models.JSONField(
        "额外选项",
        default=dict,
        blank=True,
        help_text="设置的额外选项，用于前端界面渲染",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "系统设置"
        verbose_name_plural = "系统设置"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def get_value(self) -> Any:
        """获取设置值，自动转换类型。"""
        if self.value is None:
            return self._convert_value(self.default_value)
        return self._convert_value(self.value)

    def _convert_value(self, val: Any) -> Any:
        """根据类型转换值。"""
        if val is None:
            return None

        if self.value_type == self.VALUE_TYPE.boolean:
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes", "on")
            return bool(val)

        if self.value_type == self.VALUE_TYPE.integer:
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        if self.value_type == self.VALUE_TYPE.float:
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

        if self.value_type == self.VALUE_TYPE.json:
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return {}
            return {}

        # 字符串/文本类型直接返回
        return str(val)

    def set_value(self, value: Any) -> None:
        """设置值（自动转换为字符串存储）。"""
        if value is None:
            self.value = None
            return
        if self.value_type == self.VALUE_TYPE.boolean:
            self.value = "true" if value else "false"
            return
        if self.value_type == self.VALUE_TYPE.json:
            self.value = json.dumps(value, ensure_ascii=False)
            return
        self.value = str(value)

    def validate_value(self, value: Any) -> Tuple[bool, str]:
        """验证设置值是否符合规则。"""
        import re

        rules = self.validation_rules or {}

        if rules.get("required", False) and (value is None or value == ""):
            return False, "此设置项为必填项"

        if value is None or value == "":
            return True, "验证通过"

        if self.value_type == self.VALUE_TYPE.integer:
            try:
                int(value)
            except (ValueError, TypeError):
                return False, "请输入有效的整数"
        elif self.value_type == self.VALUE_TYPE.float:
            try:
                float(value)
            except (ValueError, TypeError):
                return False, "请输入有效的数字"
        elif self.value_type == self.VALUE_TYPE.email:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                return False, "请输入有效的邮箱地址"
        elif self.value_type == self.VALUE_TYPE.url:
            url_pattern = r"^https?://"
            if not re.match(url_pattern, str(value)):
                return False, "请输入有效的URL地址（包含http://或https://）"
        elif self.value_type == self.VALUE_TYPE.json:
            try:
                json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                return False, "请输入有效的JSON格式"

        str_value = str(value)
        if "min_length" in rules and len(str_value) < rules["min_length"]:
            return False, f"长度不能少于{rules['min_length']}个字符"
        if "max_length" in rules and len(str_value) > rules["max_length"]:
            return False, f"长度不能超过{rules['max_length']}个字符"

        try:
            if "min" in rules and float(value) < rules["min"]:
                return False, f"值不能小于{rules['min']}"
            if "max" in rules and float(value) > rules["max"]:
                return False, f"值不能大于{rules['max']}"
        except (ValueError, TypeError):
            pass

        if "choices" in self.extra_options:
            choices = [c["value"] for c in self.extra_options["choices"]]
            if value not in choices:
                return False, f'值必须是以下选项之一：{", ".join(choices)}'

        return True, "验证通过"


class SettingCategory(BaseModel):
    """设置分类模型。"""

    CATEGORY = Choices(
        ("system", "系统配置"),
        ("feature", "功能开关"),
        ("ui", "界面配置"),
        ("email", "邮件配置"),
        ("security", "安全配置"),
        ("notification", "通知配置"),
        ("api", "API配置"),
        ("business", "业务配置"),
    )

    name = models.CharField("分类名称", max_length=50, choices=CATEGORY, unique=True)
    description = models.TextField("分类描述", blank=True, null=True)
    icon = models.CharField(
        "图标",
        max_length=50,
        blank=True,
        null=True,
        help_text="Bootstrap图标类名，如：bi-gear",
    )
    sort_order = models.IntegerField("排序", default=0)

    class Meta(BaseModel.Meta):
        verbose_name = "设置分类"
        verbose_name_plural = "设置分类"
        ordering = ("sort_order",) + BaseModel.Meta.ordering

    def __str__(self) -> str:
        return self.get_name_display()


__all__ = ["SystemSetting", "SettingCategory"]
