## 1. 目录结构规范 (强制执行)
每个 App 必须严格遵守以下文件分层，禁止混合职责：

- **`api.py` (接口层)**：定义 `Router`，处理 `HttpRequest`。只负责参数解析、调用 Service/Selector、返回响应。单函数建议 ≤ 30 行。
- **`schemas.py` (传输层)**：定义 Pydantic / Ninja Schema。仅用于 API 层的数据契约。
- **`services.py` (业务层)**：处理副作用（写库、外部调用）。核心业务逻辑、事务处理（`@transaction.atomic`）必须在此层。
- **`selectors.py` (查询层)**：负责数据检索（`.filter`, `.get`, 统计计算）。仅返回数据，不产生副作用。

## 2. 交互矩阵 (禁止越权)

| 调用发起方 | 可调用对象 | 严禁调用 |
| :--- | :--- | :--- |
| **API 层** | 本 App 的 Service, 本 App 的 Selector | 其他 App 的 Service/Selector/Model |
| **Service 层** | 本 App 的 Selector, **其他 App 的 Service** | 其他 App 的 Selector, 其他 App 的 Model |
| **Selector 层** | 无（仅限本 App Model 查询） | 任何 Service, 其他 App 的任何东西 |

## 3. 核心设计准则

### 3.1 解耦与聚合
- **聚合入口**：禁止在各 App 实例化 `NinjaAPI`。必须在各 App 定义 `router = Router(tags=["..."])`，并在 `config/api.py` 中通过 `api.add_router()` 统一挂载。
- **跨 App 通信**：
  - **同步调用**：App A 必须通过 App B 暴露的 `services.py` 接口获取功能，禁止直接操作 App B 的 Model 或 Selector。
  - **异步/松耦合**：对于触发式逻辑（如：用户注册成功后发送通知），必须使用 **Django Signals** 或集成事件解耦。

### 3.2 代码洁净度
- **异常处理**：Service 层抛出 `apps.core.api.exceptions` 中的自定义异常，由全局中间件统一拦截，严禁在 API 层写大量 `try...except`。
- **无状态工具**：纯技术工具（IP 获取、脱敏）放入 `apps/core/utils/`；系统级校验（手机、邮箱）放入 `apps/core/validations.py`。


分层存放权限类：

全局通用（只看 request.user 状态）放 permissions.py，如 IsAuthenticated、IsStaffOrSuperuser、IsSuperuser，避免各 App 重复。
领域特定（仅此业务需要的协议级拦截）放该 App 下，例如 permissions.py，只做基于请求的轻量判断。
涉及数据/资源关联的权限（需查询或判断资源所有者）放到业务层：services.py/selectors.py 里显式判断，而非权限类。
这样保持“全局基类在 core，领域定制在各 App，资源级权限留在 service”的清晰边界。