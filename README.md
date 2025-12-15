API使用：django-ninja
secheme使用：Django Ninja 自带 ModelSchema
# schemas.py
from ninja import ModelSchema
from myapp.models import Department

class DepartmentOut(ModelSchema):
    class Meta:
        model = Department
        fields = ['id', 'title']          # 也可 fields = "__all__" 然后 exclude = []

class DepartmentIn(ModelSchema):
    class Meta:
        model = Department
        fields = ['title']                # 创建/更新用
curd使用：django-ninja-extra
example:
# api.py
from ninja_extra import (
    ModelConfig, ModelControllerBase,
    ModelSchemaConfig, api_controller
)
from myapp.models import Department

@api_controller("/departments")               # ← 路由前缀
class DepartmentController(ModelControllerBase):
    model_config = ModelConfig(
        model=Department,
        schema_config=ModelSchemaConfig(
            read_only_fields=["id"]            # 自动生成 in/out 双 schema
        )
    )
统计：stats 也使用：django-ninja-extra-stats
example:
from ninja_extra import api_controller
from ninja_extra_stats import StatsMixin          # ← 新增
from myapp.models import Department

@api_controller("/departments")
class DepartmentController(StatsMixin, ModelControllerBase):   # 继承 StatsMixin
    model_config = ModelConfig(model=Department, ...)
