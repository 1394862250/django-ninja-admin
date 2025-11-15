# Django Ninja Admin

一个基于 Django 和 Django Ninja 的现代化管理后台系统，提供完整的用户认证、权限管理和 RESTful API 支持。

## 技术栈

### 后端技术
- **框架**: Django 5.0.3
- **API**: Django Ninja
- **数据库**: SQLite3
- **认证**: django-allauth
- **数据验证**: Pydantic
- **验证码**: django-simple-captcha

### 前端技术
- **UI 框架**: Tailwind css

### 开发工具
- **包管理**: uv
- **环境管理**: Python 虚拟环境 (.venv)
- **代码质量**: Django 内置验证器

## 功能模块

### 1. 用户认证系统
- 用户注册、登录、登出
- 邮箱验证
- 密码重置
- 验证码保护

### 2. 用户管理
- 用户信息管理
- 用户权限分配
- 用户活动记录
- 批量操作支持
- 用户资料管理（头像、昵称、性别、生日等）

### 3. 权限管理
- 基于角色的权限控制
- 细粒度权限设置
- 权限继承机制
- 自定义权限支持

### 4. 通知系统
- 系统通知发布
- 通知历史记录
- 批量通知功能
- 通知状态管理

### 5. 数据可视化
- 用户统计图表
- 活动数据分析
- 系统性能监控
- 自定义报表功能

### 6. API 文档
- 自动生成的 API 文档
- 交互式 API 测试界面
- 完整的请求/响应示例

## 项目结构

```
django-ninja-admin/
├── app/                    # 应用主目录
│   ├── middleware/         # 中间件
│   ├── notification/       # 通知模块
│   ├── user/              # 用户模块
│   │   ├── api/           # API 接口
│   │   ├── migrations/    # 数据库迁移
│   │   ├── model.py       # 数据模型
│   │   ├── schemas.py     # 数据验证模式
│   │   └── signals.py     # 信号处理器
│   ├── utils/             # 工具函数
│   └── web/               # Web 视图
├── static/                # 静态文件
├── templates/             # 模板文件
├── media/                 # 用户上传文件
├── system/                # 系统配置
└── manage.py              # Django 管理脚本
```

## 快速开始

### 环境要求
- Python 3.8+
- uv (最新版本)

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/1394862250/django-ninja-admin.git
cd django-ninja-admin
```

2. 创建虚拟环境并安装依赖
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. 数据库迁移
```bash
python manage.py migrate
```

4. 创建超级用户
```bash
python manage.py createsuperuser
```

5. 下载静态资源
```bash
python manage.py download_static
```

6. 启动开发服务器
```bash
python manage.py runserver
```

7. 访问应用
- 前端界面: http://127.0.0.1:8000/
- 管理后台: http://127.0.0.1:8000/admin/
- API 文档: http://127.0.0.1:8000/api/docs/

## 开发指南

### API 设计
- 遵循 RESTful 设计原则
- 使用 Pydantic 进行数据验证
- 统一的错误处理机制
- 完整的 API 文档

### 测试
```bash
# 运行所有测试
python manage.py test

# 运行特定模块测试
python manage.py test app.user
```

## 部署

### 生产环境配置
1. 设置环境变量
2. 配置数据库
3. 收集静态文件
4. 配置 Web 服务器（Nginx/Apache）
5. 配置 WSGI 服务器（Gunicorn/uWSGI）

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
