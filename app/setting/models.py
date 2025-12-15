"""设置模型"""
from django.db import models
from model_utils import Choices
from model_utils.models import TimeStampedModel


class SystemSetting(TimeStampedModel):
    """系统设置模型"""

    # 设置类型
    VALUE_TYPE = Choices(
        ('boolean', '布尔值'),
        ('integer', '整数'),
        ('float', '浮点数'),
        ('string', '字符串'),
        ('text', '长文本'),
        ('json', 'JSON数据'),
        ('url', 'URL地址'),
        ('email', '邮箱地址'),
    )

    # 设置分类
    CATEGORY = Choices(
        ('system', '系统配置'),
        ('feature', '功能开关'),
        ('ui', '界面配置'),
        ('email', '邮件配置'),
        ('security', '安全配置'),
        ('notification', '通知配置'),
        ('api', 'API配置'),
        ('business', '业务配置'),
    )

    # 设置键名（唯一）
    key = models.CharField(
        '设置键名',
        max_length=100,
        unique=True,
        help_text='设置的唯一标识符，使用点分命名法，如：system.site_name'
    )

    # 设置名称
    name = models.CharField(
        '设置名称',
        max_length=200,
        help_text='设置的显示名称'
    )

    # 设置值类型
    value_type = models.CharField(
        '值类型',
        max_length=20,
        choices=VALUE_TYPE,
        default=VALUE_TYPE.string,
        help_text='设置值的数据类型'
    )

    # 设置分类
    category = models.CharField(
        '分类',
        max_length=20,
        choices=CATEGORY,
        default=CATEGORY.system,
        help_text='设置的分类'
    )

    # 设置值
    value = models.TextField(
        '设置值',
        blank=True,
        null=True,
        help_text='设置的实际值'
    )

    # 默认值
    default_value = models.TextField(
        '默认值',
        blank=True,
        null=True,
        help_text='设置的默认值'
    )

    # 设置描述
    description = models.TextField(
        '描述',
        blank=True,
        null=True,
        help_text='设置的详细说明'
    )

    # 是否启用
    is_active = models.BooleanField(
        '是否启用',
        default=True,
        help_text='是否启用此设置项'
    )

    # 是否可编辑
    is_editable = models.BooleanField(
        '是否可编辑',
        default=True,
        help_text='是否允许通过界面编辑'
    )

    # 排序
    sort_order = models.IntegerField(
        '排序',
        default=0,
        help_text='设置项在界面中的显示顺序，数值越小越靠前'
    )

    # 验证规则（JSON格式）
    validation_rules = models.JSONField(
        '验证规则',
        default=dict,
        blank=True,
        help_text='设置的验证规则，如：{"min": 0, "max": 100, "required": true}'
    )

    # 额外选项（JSON格式）
    # 例如：{'choices': [{'value': 'a', 'label': '选项A'}, {'value': 'b', 'label': '选项B'}]}
    # 或者：{'placeholder': '请输入...', 'max_length': 255}
    extra_options = models.JSONField(
        '额外选项',
        default=dict,
        blank=True,
        help_text='设置的额外选项，用于前端界面渲染'
    )

    class Meta:
        verbose_name = '系统设置'
        verbose_name_plural = '系统设置'
        ordering = ['category', 'sort_order', 'key']

    def __str__(self):
        return f'{self.name} ({self.key})'

    def get_value(self):
        """获取设置值，自动转换类型"""
        if self.value is None:
            return self._convert_value(self.default_value)
        return self._convert_value(self.value)

    def _convert_value(self, val):
        """根据类型转换值"""
        if val is None:
            return None

        if self.value_type == self.VALUE_TYPE.boolean:
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('true', '1', 'yes', 'on')
            return bool(val)

        elif self.value_type == self.VALUE_TYPE.integer:
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        elif self.value_type == self.VALUE_TYPE.float:
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

        elif self.value_type == self.VALUE_TYPE.json:
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                try:
                    import json
                    return json.loads(val)
                except json.JSONDecodeError:
                    return {}
            return {}

        # 字符串类型直接返回
        return str(val)

    def set_value(self, value):
        """设置值（自动转换为字符串存储）"""
        if value is None:
            self.value = None
        elif self.value_type == self.VALUE_TYPE.boolean:
            self.value = 'true' if value else 'false'
        elif self.value_type == self.VALUE_TYPE.json:
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)

    def validate_value(self, value):
        """验证设置值是否符合规则"""
        import re
        import json

        # 获取验证规则
        rules = self.validation_rules or {}

        # 必填验证
        if rules.get('required', False) and (value is None or value == ''):
            return False, '此设置项为必填项'

        # 如果值为空且不是必填，跳过其他验证
        if value is None or value == '':
            return True, '验证通过'

        # 类型验证
        if self.value_type == self.VALUE_TYPE.integer:
            try:
                int(value)
            except (ValueError, TypeError):
                return False, '请输入有效的整数'
        elif self.value_type == self.VALUE_TYPE.float:
            try:
                float(value)
            except (ValueError, TypeError):
                return False, '请输入有效的数字'
        elif self.value_type == self.VALUE_TYPE.email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                return False, '请输入有效的邮箱地址'
        elif self.value_type == self.VALUE_TYPE.url:
            url_pattern = r'^https?://'
            if not re.match(url_pattern, str(value)):
                return False, '请输入有效的URL地址（包含http://或https://）'
        elif self.value_type == self.VALUE_TYPE.json:
            try:
                json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                return False, '请输入有效的JSON格式'

        # 长度验证
        str_value = str(value)
        if 'min_length' in rules and len(str_value) < rules['min_length']:
            return False, f'长度不能少于{rules["min_length"]}个字符'
        if 'max_length' in rules and len(str_value) > rules['max_length']:
            return False, f'长度不能超过{rules["max_length"]}个字符'

        # 数值范围验证
        try:
            if 'min' in rules and float(value) < rules['min']:
                return False, f'值不能小于{rules["min"]}'
            if 'max' in rules and float(value) > rules['max']:
                return False, f'值不能大于{rules["max"]}'
        except (ValueError, TypeError):
            pass

        # 选择项验证
        if 'choices' in self.extra_options:
            choices = [c['value'] for c in self.extra_options['choices']]
            if value not in choices:
                return False, f'值必须是以下选项之一：{", ".join(choices)}'

        return True, '验证通过'


class SettingCategory(TimeStampedModel):
    """设置分类模型"""

    CATEGORY = Choices(
        ('system', '系统配置'),
        ('feature', '功能开关'),
        ('ui', '界面配置'),
        ('email', '邮件配置'),
        ('security', '安全配置'),
        ('notification', '通知配置'),
        ('api', 'API配置'),
        ('business', '业务配置'),
    )

    name = models.CharField(
        '分类名称',
        max_length=50,
        choices=CATEGORY,
        unique=True
    )

    description = models.TextField(
        '分类描述',
        blank=True,
        null=True
    )

    icon = models.CharField(
        '图标',
        max_length=50,
        blank=True,
        null=True,
        help_text='Bootstrap图标类名，如：bi-gear'
    )

    sort_order = models.IntegerField(
        '排序',
        default=0
    )

    class Meta:
        verbose_name = '设置分类'
        verbose_name_plural = '设置分类'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.get_name_display()
