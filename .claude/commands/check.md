# AI 违规行为检查清单（Code Review 必查）

> 本清单用于 **人工 Review / AI 自检 / 未来自动化检查**  
> 目标是：**防止架构漂移、权限失控、复杂度失控**

---

## 一、Communication & Documentation 违规（P2）

### ❌ 违规行为
- 出现英文注释或英文说明
- `.md` 文档未使用中文
- 正式文档未放入 `docs/`
- 讨论 / 方案 / 评审类文档未放入 `discuss/`

### ✅ 检查方式
- 浏览代码与文档
- 检查文件路径

---

## 二、关键字级违规（文本扫描级，等价 grep，P0）

### ❌ 一票否决（出现即重写）

出现以下任一关键词（不区分大小写）：

- `rbac`
- `role`
- `permission`
- `policy`

出现以下类名 / 架构概念：

- `Service`
- `Repository`
- `DDD`
- `Domain Driven`
- `Clean Architecture`
- `Hexagonal`

### ✅ 检查方式
- 全局搜索关键词
- AI 自检：是否引入未被允许的概念

---

## 三、目录结构违规（等价 grep，P0）

### ❌ 一票否决

- 出现以下目录或文件：
  - `services/`
  - `repositories/`
  - `domain/`
  - `usecase/`（非 `flows/`）
- Flow 不在 `flows/` 目录
- Action 不在 `actions/` 目录
- API 中 `import actions`
- API 直接调用 Action

### ✅ 检查方式
- 查看目录结构
- 检查 import 语句

---

## 四、架构级违规（必须 0 容忍，P0）

### ❌ 一票否决

- 定义 `Service` 类 / `xxxService`
- 定义 `Repository` 类
- 使用接口 + 实现类的三层结构
- 出现业务类（非 ORM Model）
- 使用装饰器 / 框架级方式表达业务规则

---

## 五、Flow 违规（等价 grep + ruff，P1）

### ❌ 必须整改

- Flow 中出现：
  - `obj.field = ...`
  - `.save()`
  - `.delete()`
- Flow 中直接写实现细节而非流程
- Flow 超过 300 行但未拆分
- Flow 绕过 Action 直接改数据

### ✅ 正确对照形态

```python
def xxx_flow(...):
    # 权限检查
    # 调用 action
    # 条件分支
    # 后处理
````

---

## 六、Action 违规（等价 grep + ruff，P1）

### ❌ 必须整改

* Action 中出现：

  * `for`
  * `while`
  * `try / except`
  * 多分支 `if / elif / else`
* Action 中访问 request / response / HTTP
* Action 中包含权限判断
* 单个 Action 超过 30 行

### ✅ 正确对照形态

```python
def rename_project(project, name):
    project.name = name
    project.save()
```

---

## 七、权限设计违规（P0 / P1）

### ❌ 一票否决（P0）

* 使用 RBAC / Role / Permission / Policy
* 使用装饰器实现权限
* 使用框架级权限系统
* 权限逻辑不在 Flow 中

### ❌ 必须整改（P1）

* 权限判断不属于以下三种之一：

  1. `user.id == resource.owner_id`
  2. resource member 表中的 boolean 字段
  3. `user.is_staff / user.is_superuser`
* 同一权限逻辑在多个 Flow 中复制粘贴
* 复杂权限未封装为 `can_xxx` 函数

---

## 八、API 层违规（P1）

### ❌ 必须整改

* API 中：

  * 写业务逻辑
  * 写权限判断
  * 直接调用 Action
* 单个 API 超过 30 行
* API 未调用 Flow

### ✅ 正确对照形态

```python
@api.post("/xxx")
def api_xxx(request, payload):
    return xxx_flow(request.user, payload)
```

---

## 九、命名规范违规（等价 pylint，P2）

### ❌ 建议整改

* Flow 未以 `_flow` 结尾
* Action 未以动词开头
* Validation 未以 `validate_` 开头
* 函数名无法读成一句清晰的业务动作

---

## 十、规模与复杂度违规（等价 ruff / pylint）

### ❌ 必须整改（P1）

* 单个 Flow：

  * 超过 300 行
  * 出现多个 try / except
  * 出现多个外部系统调用但未拆子 Flow

### ❌ 建议整改（P2）

* 单文件逻辑密集但未拆分
* 多处出现高度相似的业务逻辑

---

## 十一、AI 行为违规（极其重要）

### ❌ 一票否决（P0）

* AI 自行引入新架构
* AI 自行扩展需求
* AI 在需求存在歧义时未先澄清而直接实现

### ❌ 必须整改（P1）

* AI 未先给出目录结构
* AI 未按 Action → Flow → API 顺序输出代码

---

## 十二、人工 Review 快速检查法（30 秒）

> 只回答下面 5 个问题：

1. 有没有出现 RBAC / Service / Repository？
2. API 有没有只调用 Flow？
3. Flow 看起来像流程图吗？
4. Action 看起来像原子操作吗？
5. 权限能不能一句话读懂？

**任意一项不通过 → 直接打回**

---

## 十三、违规分级说明

| 级别 | 含义               |
| -- | ---------------- |
| P0 | 原则性错误，必须重写       |
| P1 | 结构性问题，必须整改       |
| P2 | 风格 / 可维护性问题，建议优化 |
