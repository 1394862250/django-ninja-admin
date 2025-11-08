#!/bin/bash

# Django数据库迁移脚本
echo "执行Django数据库迁移..."

# 激活虚拟环境
source .venv/Scripts/activate

# 设置Django环境变量
export DJANGO_SETTINGS_MODULE=system.settings
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 执行迁移
python manage.py makemigrations
python manage.py migrate

echo "数据库迁移完成！"