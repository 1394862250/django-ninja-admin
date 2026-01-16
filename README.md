# Django Ninja Admin

基于 Django + Django Ninja Extra 的轻量后台示例，遵循 Service/Selector 架构约束。

## 项目概览
- **核心框架**：Django 5.0 + Django Ninja Extra (提供优雅的 API 开发体验)
- **认证授权**：django-allauth + django-guardian (对象级权限)
- **数据层**：Pydantic v2 (Ninja) 数据验证
- **UI 组件**：现代化的管理后台模板，集成 Tailwind CSS + jQuery
- **扩展功能**：django-simple-captcha (验证码)、psutil (系统监控)、faker (测试数据生成)

## 架构约定 (强制遵守)

项目遵循严谨的分层设计，确保逻辑清晰且易于测试：

1.  **API 层 (`api.py`)**：定义 `Router`，处理 HTTP 请求/响应，只负责参数解析、调用 Service/Selector。
2.  **传输层 (`schemas.py`)**：定义 Pydantic / Ninja Schema，用于数据交换契约。
3.  **业务层 (`services.py`)**：处理所有**副作用**（写数据库、发送消息、调用外部 API）。
4.  **查询层 (`selectors.py`)**：负责所有**数据检索**（Filter、Get、统计）。严禁修改数据。
5.  **核心层 (`apps/core/`)**：存放全局中间件、自定义异常、权限基类及无状态工具函数。

## 交互矩阵 (禁止越权)

| 调用发起方 | 可调用对象 | 严禁调用 |
| :--- | :--- | :--- |
| **API 层** | 本 App 的 Service, 本 App 的 Selector | 其他 App 的 Service/Selector/Model |
| **Service 层** | 本 App 的 Selector, **其他 App 的 Service** | 其他 App 的 Selector, 其他 App 的 Model |
| **Selector 层** | 无（仅限本 App Model 查询） | 任何 Service, 其他 App 的任何东西 |

## 目录结构
```bash
apps/
  ├── core/            # 全局核心组件（中间件、异常、通用工具）
  ├── user/            # 用户领域（认证、用户管理）
  ├── log/             # 日志领域（操作日志记录）
  ├── notification/    # 通知领域（系统消息、推送）
  ├── setting/         # 系统设置（全局动态配置）
  └── web/             # 传统页面视图 (HTML Templates)
system/                # Django 项目配置 (settings, urls, wsgi)
static/                # 静态资源 (CSS, JS, Fonts)
templates/             # HTML 模板文件
```

## 快速开始

### 1. 环境准备
使用 `uv` 或 `pip` 管理依赖：
```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化项目
```bash
# 拷贝环境配置 (如果存在 .env.example)
# cp .env.example .env

# 执行数据库迁移
python manage.py migrate

# 创建超级管理员
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

## 常用入口
- **后台管理**：[http://127.0.0.1:8000/manage/](http://127.0.0.1:8000/manage/)
- **API 文档 (Swagger)**：[http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **登录页面**：[http://127.0.0.1:8000/auth/login/](http://127.0.0.1:8000/auth/login/)