"""日志Schema定义"""
from ninja import Schema
from typing import Optional, Dict, Any
from datetime import datetime


class LogSchema(Schema):
    """日志Schema"""
    id: int
    level: str
    category: str
    user_id: Optional[int] = None
    user_username: Optional[str] = None
    action: str
    message: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    extra_data: Dict[str, Any] = {}
    created: datetime
    modified: datetime


class LogCreateSchema(Schema):
    """创建日志Schema"""
    level: str
    category: str
    action: str
    message: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = {}


class LogFilterSchema(Schema):
    """日志查询过滤Schema"""
    level: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
