#!/bin/bash

# Django开发服务器启动脚本
echo "启动Django开发服务器..."

# 激活虚拟环境
source .venv/Scripts/activate

# 设置Django环境变量
export DJANGO_SETTINGS_MODULE=system.settings
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 创建logs目录（如果不存在）
mkdir -p logs

# 启动Django开发服务器
python manage.py runserver 0.0.0.0:8000