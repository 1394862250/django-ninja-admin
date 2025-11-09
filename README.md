# Django Ninja Admin - V1.0.0.5

![Version](https://img.shields.io/badge/version-1.0.0.5-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0.3-green.svg)
![Django Ninja](https://img.shields.io/badge/Django%20Ninja-1.4.5-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)

一个基于现代Django技术栈的管理后台系统，采用微服务架构和Django Ninja API框架。

## 🚀 版本历史

- **V1.0.0.5** (当前版本) - 通知模块版本
- **V1.0.0.4** - 完整工具集成版本
- **V1.0.0.3** - Django Ninja微服务架构版本
- **V1.0.0.2** - 传统Django视图版本
- **V1.0.0.1** - 基础版本

## 📋 版本更新说明

### 🔄 V1.0.0.5 主要变更

V1.0.0.5 在 V1.0.0.4 的基础上新增了**通知模块**，进一步完善了企业级管理后台的功能。

#### 新增功能模块

1. **通知模块 (Notification Module)**
   - 完整的站内通知系统
   - 支持通知分类、优先级、状态管理
   - 未读通知计数
   - 批量标记已读功能
   - 计划发送时间支持

### 🔄 V1.0.0.4 主要变更

V1.0.0.4是对V1.0.0.3的重大升级，添加了完整的Django生态系统工具集成，显著提升了系统的功能性和企业级特性。

### 🛠️ 新增集成工具

#### 1. **Django Guardian** - 对象级权限控制
- **新增功能**: 细粒度的用户权限管理
- **使用方法**: 
  ```python
  from guardian.shortcuts import assign_perm, get_perms
  # 为用户分配对象权限
  assign_perm('change_userprofile', user, profile_instance)
  ```

#### 2. **Django Allauth** - 完整认证系统
- **新增功能**: 高级用户认证和账户管理
- **新路由**: `/accounts/` 下的所有认证相关页面
- **使用方法**: 
  ```python
  # 邮箱验证
  ACCOUNT_EMAIL_VERIFICATION = 'optional'
  # 社交登录支持
  SOCIALACCOUNT_PROVIDERS = {
      'google': {
          'SCOPE': ['profile', 'email'],
      }
  }
  ```

#### 3. **Django ImageKit** - 图片处理系统
- **新增功能**: 自动图片处理和优化
- **新字段**: 
  ```python
  avatar = ProcessedImageField(
      upload_to='avatars/',
      processors=[ResizeToFit(300, 300)],
      format='JPEG',
      options={'quality': 90}
  )
  ```

#### 4. **Django Model Utils** - 模型工具增强
- **新增功能**: 高级模型功能
- **新模型**: TimeStampedModel, StatusModel, Choices
- **使用方法**:
  ```python
  from model_utils.models import TimeStampedModel, StatusModel
  from model_utils import Choices
  
  STATUS_CHOICES = Choices('active', 'inactive', 'suspended')
  ```

### 📊 API功能扩展

#### V1.0.0.5 新增API接口

**通知模块 API (6个):**
- `GET /api/notifications` - 获取通知列表（支持分页、过滤：category、status、is_read）
- `GET /api/notifications/unread-count` - 获取当前用户未读通知数量
- `POST /api/notifications/mark-read/{notification_id}` - 标记单个通知为已读
- `POST /api/notifications/mark-read-bulk` - 批量标记通知为已读
- `POST /api/notifications` - 创建通知（需要管理员权限）
- `DELETE /api/notifications/{notification_id}` - 删除通知

#### V1.0.0.4 新增API接口 (4个):
- `POST /api/user/upload-avatar` - 头像上传和自动处理
- `GET /api/user/activities` - 用户活动记录查询
- `POST /api/user/update-profile` - 增强版个人资料更新
- `GET /api/user/change-password` - 密码修改页面信息

**增强的API功能:**
- 自动活动记录系统
- 扩展用户信息返回
- 权限检查和验证
- 图片自动处理
- 通知系统集成

### 🏗️ 架构改进

#### 微服务结构优化
```
app/
├── middleware/          # 中间件系统
│   ├── auth_middleware.py
│   └── cors_middleware.py
├── utils/              # 工具定义
│   ├── validators.py   # 数据验证器
│   └── responses.py    # 响应格式
├── notification/       # 通知微服务 (V1.0.0.5新增)
│   ├── api.py          # 通知API接口
│   ├── model.py        # 通知模型
│   ├── schema.py       # 通知数据模式
│   └── tests/          # 通知测试
├── user/               # 用户微服务
│   ├── api.py          # 用户管理API
│   ├── model.py        # 用户模型
│   ├── app.py          # 应用配置
│   └── test.py         # 测试用例
└── web/                # Web视图应用
    ├── urls.py
    └── views.py
```

### 📁 配置文件更新

#### system/settings.py
新增配置:
```python
# Allauth配置
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# ImageKit配置
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'imagekit.backends.cacheback.ImageSpecField'
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.strategies.cacheback.cached_writes'

# Model Utils配置
MODEL_UTILS_USE_TZ = True
```

#### system/urls.py
新增路由:
```python
# 导入通知API
from app.notification.api import api as notification_api

# 注册通知API
api.add_router("", notification_api)

path('accounts/', include('allauth.urls')),  # Allauth认证路由
```

### 🗄️ 数据库变化

#### 新增数据表

**V1.0.0.5 新增表 (1个):**
- **Notification**: 通知表

**V1.0.0.5 新增迁移文件:**
- `notification/migrations/0001_initial.py` - 通知模块初始迁移

**V1.0.0.4 新增表 (14个):**
- **Allauth表 (5个)**: 邮箱验证、社交账户等
- **Guardian表 (3个)**: 对象权限管理
- **Social Account表 (6个)**: 社交登录支持
- **扩展表 (3个)**: UserProfile, UserActivity, DocumentUpload

### 🎯 新功能特性

#### V1.0.0.5 新增功能

**1. 通知管理系统**
- 完整的站内通知功能
- 支持通知分类（category）
- 优先级管理（低/中/高）
- 状态跟踪（待发送/已发送/发送失败）
- 未读通知计数
- 批量操作支持
- 计划发送时间
- 元数据存储

#### V1.0.0.4 新增功能

**1. 用户活动记录系统**
- 自动记录所有用户操作
- 支持多种活动类型
- 包含IP和用户代理信息
- 支持元数据存储

**2. 智能图片处理**
- 自动头像缩略图生成
- 图片格式转换和优化
- 动态图片处理
- 缓存优化

**3. 扩展用户系统**
- 详细个人资料（昵称、性别、出生日期）
- 状态管理
- 统计信息
- 自动昵称生成

**4. 文档管理系统**
- 文件上传处理
- 自动缩略图生成
- 访问控制
- 类型验证

### 🔧 迁移步骤

#### 1. **依赖更新**
```bash
# 使用 uv 安装依赖（推荐）
uv sync

# 或使用传统方式
pip install -r requirements.txt
```

#### 2. **数据库迁移**
```bash
# 使用 uv 运行迁移
uv run python manage.py migrate

# 或使用脚本
bash scripts/migrate.sh
```

#### 3. **创建超级用户**
```bash
# 使用 uv 运行
uv run python manage.py createsuperuser

# 或使用传统方式
python manage.py createsuperuser
```

#### 4. **配置更新**
- 更新`system/settings.py`中的新配置
- 更新`system/urls.py`中的新路由

### 📚 API文档

#### 新的API端点

**认证相关 (3个)**
- `POST /api/auth/login` - 增强版登录
- `POST /api/auth/register` - 增强版注册
- `POST /api/auth/logout` - 增强版登出

**用户相关 (6个)**
- `GET /api/user/profile` - 获取用户信息
- `GET /api/user/home` - 用户首页
- `POST /api/user/change-password` - 修改密码
- `POST /api/user/upload-avatar` - 上传头像
- `GET /api/user/activities` - 活动记录
- `POST /api/user/update-profile` - 更新资料

**通知相关 (6个) - V1.0.0.5新增**
- `GET /api/notifications` - 通知列表（支持过滤和分页：category、status、is_read）
- `GET /api/notifications/unread-count` - 未读通知数量
- `POST /api/notifications/mark-read/{notification_id}` - 标记单个通知已读
- `POST /api/notifications/mark-read-bulk` - 批量标记已读
- `POST /api/notifications` - 创建通知（需要管理员权限）
- `DELETE /api/notifications/{notification_id}` - 删除通知

**管理相关 (9个)**
- `GET /api/admin/dashboard` - 管理面板
- `GET /api/admin/users` - 用户列表
- `GET /api/admin/users/{id}` - 用户详情
- `POST /api/admin/users` - 创建用户
- `PUT /api/admin/users/{id}` - 更新用户
- `DELETE /api/admin/users/{id}` - 删除用户
- `POST /api/admin/users/{id}/toggle-status` - 切换状态

**Web界面 (新增)**
- `/accounts/login/` - Allauth登录页面
- `/accounts/signup/` - Allauth注册页面
- `/accounts/logout/` - Allauth登出页面
- `/admin/` - Django管理后台

### 🧪 测试

#### 运行测试
```bash
# 使用 uv 运行测试
uv run python manage.py test app.user.test
uv run python manage.py test app.notification.tests

# 或使用传统方式
python manage.py test app.user.test
python manage.py test app.notification.tests
```

### 🚀 启动项目

#### 开发环境启动
```bash
# 使用 uv 启动（推荐）
uv run python manage.py runserver 0.0.0.0:8000

# 或使用脚本
bash scripts/run_server.sh

# 传统方式
.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

#### 访问地址
- **主页**: http://127.0.0.1:8000/
- **API文档**: http://127.0.0.1:8000/api/docs/
- **管理后台**: http://127.0.0.1:8000/admin/
- **用户认证**: http://127.0.0.1:8000/accounts/

### 📖 文档链接

- [API文档](http://127.0.0.1:8000/api/docs/)
- [Django Ninja文档](https://django-ninja.rest/)
- [Django Allauth文档](https://django-allauth.readthedocs.io/)
- [Django Guardian文档](https://django-guardian.readthedocs.io/)
- [Django ImageKit文档](https://django-imagekit.readthedocs.io/)

### 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

### 📄 许可证

本项目采用MIT许可证。

---

## 📝 使用示例

### 通知模块使用示例

```python
# 创建通知
POST /api/notifications
{
    "recipient_id": 1,
    "title": "系统通知",
    "body": "您有一条新消息",
    "category": "system",
    "priority": "high"
}

# 获取未读通知数量
GET /api/notifications/unread-count

# 标记通知已读
POST /api/notifications/mark-read/1
```

---

**升级至V1.0.0.5后，您将获得一个功能完整的企业级Django管理后台系统，包含通知系统功能！** 🎉