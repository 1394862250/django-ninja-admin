> Django Ninja Admin · 基于 Django + Django Ninja Extra 的轻量后台示例，遵守 Action/Flow 架构约束。

## 项目概览
- 框架：Django 5 + Django Ninja Extra（自动 CRUD / Controller）
- 认证：django-allauth
- 验证码：django-simple-captcha
- 组件：model_utils、ninja-schema、pydantic 校验

## 架构约定（必须遵守）
- API/Router 层：仅做参数解析与响应包装；**只调用 Flow，不直接调用 Action**。
- Flow 层：编排业务与权限判断（显式 `if`）；可调用多个 Action；不直接改 ORM。
- Action 层：原子数据库操作，单一职责，无循环/try/多分支。
- Model 层：仅存储与模型相关的字段/校验。
- Middleware：只做请求/响应拦截与数据收集，不含业务。
- Utils：仅通用工具，不含业务或权限。

## 目录结构
```
app/
  log/            # 日志微服务（flows/actions/api/model）
  notification/   # 通知微服务（flows/actions/api/model）
  setting/        # 系统设置微服务（flows/actions/api/model）
  user/           # 用户微服务（auth/admin/feature flows/actions/api）
  middleware/     # 中间件（无业务）
  utils/          # 通用工具（无业务逻辑）
  web/            # 传统页面视图与模板
system/           # Django 配置
```

## 快速开始
```bash
# 1) 创建虚拟环境（示例）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) 安装依赖
pip install -r requirements.txt

# 3) 初始化数据库
python manage.py migrate

# 4) 启动开发服务器
python manage.py runserver
```

## 测试
```bash
python manage.py test
```

## 常用入口
- 前端页面：`/`、`/manage/`
- API 文档（Ninja Extra）：`/api/docs/`

