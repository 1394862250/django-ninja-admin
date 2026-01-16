"""时间与耗时相关的轻量工具。"""
import datetime
from typing import Union


def now() -> datetime.datetime:
    """当前UTC时间（可扩展为带时区配置）。"""
    return datetime.datetime.utcnow()


def duration_ms(start: Union[int, float], end: Union[int, float]) -> int:
    """计算耗时毫秒数。"""
    return int((end - start) * 1000)


__all__ = ["now", "duration_ms"]
