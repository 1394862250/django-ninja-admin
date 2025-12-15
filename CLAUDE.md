# 项目强制工程规范（AI 必须严格遵守）

---

## Communication

- 永远使用简体中文进行思考和对话

---

## Documentation

- 一般不主动编写 .md 文档，除非我明确要求
- 正式文档写入 docs/
- 讨论 / 评审类文档写入 discuss/
- 系统日志统一存储到 logs/

---

## 开发环境约定

- MySQL 默认账号密码：root / root
- Python 项目必须使用虚拟环境
- 默认使用 uv 管理依赖（没有则先安装）

---

## 权限设计约束（零容忍）

- 禁止使用 RBAC / Role / Permission / Policy
- 禁止新增任何权限相关表
- 权限判断只允许以下三种：
  1. user.id == resource.owner_id
  2. resource member 表中的 boolean 字段
  3. user.is_staff / user.is_superuser
- 权限必须使用显式 if 判断
- 禁止装饰器 / 框架级权限系统
- 权限逻辑必须写在 Flow 中

---

## 后端架构总则（必须遵守）

- 使用 Flow / Action 架构（函数编排式 MVC）
- 禁止三层架构（Controller / Service / Repository）
- 禁止 DDD / Clean Architecture / Hexagonal
- 不定义 Service / Repository
- 所有业务逻辑使用函数实现，不使用业务类

---

## 分层职责（强制）

### API / Router

- 只负责参数解析与返回
- 禁止业务逻辑与权限判断
- 只允许调用 Flow，禁止调用 Action
- 单个 API ≤ 30 行

---

### Flow（Use Case）

- 一个 Flow 表示一个完整业务用例
- 只负责编排流程（调用 Action）
- 允许 if / for / try
- 权限判断必须写在 Flow 中
- 禁止直接修改 ORM 字段
- 所有数据变更必须通过 Action
- 单个 Flow ≤ 300 行

---

### Action（Domain Action）

- 原子业务操作，单一职责
- 不包含流程控制
- 不依赖 HTTP / Request
- 禁止出现：
  - for / while
  - try / except
  - 多分支 if（允许单个校验式 if）
- 单个 Action ≤ 30 行

---

## Schema 规则（强制）

- Schema 是 API 与 Flow 的边界数据结构
- Schema 只允许存在于 api/ 下
- Schema 只用于 API 层，不得进入 Flow / Action
- Schema 禁止：
  - 业务逻辑
  - 权限判断
  - 数据库查询
  - 调用 Flow / Action
- 禁止 Base / Common / Shared Schema
- Schema 不允许继承
- Schema 只定义接口所需的最小字段

### 命名规范

- CreateXxxIn / UpdateXxxIn
- ListXxxQuery
- XxxOut

---

## ORM 使用规范

- ORM Model 仅用于数据存储
- 禁止在 Model 中写业务、权限或流程逻辑

---

## 项目目录结构（强制）

```

project/
├── api/
├── flows/
├── actions/
├── models.py

```

---

## 复杂度控制规则

- 任意业务逻辑 > 50 行必须拆分
- 稳定逻辑 → Action
- 流程编排 → Flow
- 复杂权限 → can_xxx 函数
- 禁止在 Flow 中复制粘贴权限逻辑

---

## Flow 拆分强制条件

当 Flow 出现以下任一情况，必须拆分为子 Flow：

- 连续 3 个以上业务阶段
- 多个 try / except
- 多个外部系统调用

---

## 实现顺序（强制）

1. 定义目录结构
2. 实现 Action
3. 实现 Flow
4. 实现 API（绑定 Schema）

---

## 命名规范（强制）

- Flow：<verb>_<resource>_flow
- Action：<verb>_<resource>
- Validation：validate_<thing>
- 权限函数：can_<action>_<resource>

---

## Java 项目补充说明（强制）

- Flow / Action 使用普通类表示
- Flow 类名必须以 Flow 结尾
- Action 类名必须以 Action 结尾
- 禁止使用 @Service / @Repository
- 禁止定义 Repository 接口
- 禁止使用 AOP / 拦截器实现业务或权限
- Schema 使用 DTO / record，仅用于 API 层

---

## Python 项目补充说明（强制）

- Flow / Action 必须使用函数实现
- 禁止使用 Service / Manager / Handler 类
- 禁止三层或伪三层结构
- API 只能调用 Flow
- 禁止 DRF / Serializer / ViewSet
- Schema 使用 Pydantic / Ninja Schema，仅用于 API 层

---

## 资源型接口豁免规则（重要）

以下接口允许不使用 Flow / Action：

- 纯 CRUD
- 无业务语义的列表 / 查询 / 统计
- 无副作用、无复杂权限的管理接口

一旦出现以下情况，必须使用 Flow：

- 多步骤业务逻辑
- 权限判断（owner / member）
- 有业务语义的状态变更
- 事务 / 回滚 / 外部系统调用

---

## Response / 工具边界规则（强制）

- 允许统一 Response 外壳（如 ok / fail）
- 禁止 BaseResponse[T] 或强制统一返回 Schema
- Response 工具仅存在于 api/ 层

- 禁止将业务逻辑放入 utils / helpers / common
- 函数名包含业务名词即视为业务
- payment / ai / wechat / 第三方集成一律视为业务
- 流程 → flows/，外部调用 → actions/
- 禁止 wechat.py / payment.py / ai.py 等伪工具模块

---

## Middleware 使用规范（强制）

- 中间件仅用于协议级、横切关注点
- 仅允许：
  - CORS
  - 请求 / 访问日志
  - TraceID / RequestID
  - 性能统计
- 禁止：
  - 业务逻辑
  - 权限判断
  - 数据库读写
  - 调用 Flow / Action
- 中间件不得影响业务流程
- log_middleware 只记录路径、方法、状态码、耗时

---

## 前端代码体积约束（强制）

- 单组件 ≤ 150 行，超出必须拆分
- 禁止样式状态变量
- 禁止为未来复用提前抽象
- 每个组件必须一句话说明职责