"""
Web应用的模板标签和过滤器
"""
from django import template

register = template.Library()

@register.filter
def has_permission_type(permissions, perm_type):
    """检查权限列表中是否包含指定类型的权限"""
    if not permissions:
        return False
    # 处理权限对象或字典
    if hasattr(permissions, 'all'):
        permissions = permissions.all()
    
    # 如果是查询集，转换为列表
    if hasattr(permissions, '__iter__') and not isinstance(permissions, (list, tuple)):
        permissions = list(permissions)
    
    # 如果是字典列表，直接使用
    if isinstance(permissions, list) and permissions and hasattr(permissions[0], 'get'):
        return any(perm.get('permission_type') == perm_type for perm in permissions)
    
    # 如果是模型对象列表，使用getattr
    return any(getattr(perm, 'permission_type', None) == perm_type for perm in permissions)
