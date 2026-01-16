"""用户模块只读查询与校验。"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional, Tuple
from uuid import UUID

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.utils import timezone

from apps.core.utils.serializers import to_iso
from .model import Role, UserActivity, UserProfile

User = get_user_model()


# 基础查询
def base_user_queryset() -> QuerySet:
    return User.objects.filter(is_deleted=False)


def authenticate_user(username: str, password: str):
    """认证用户。"""
    return authenticate(username=username, password=password)


def check_user_exists_by_username(username: str) -> bool:
    return base_user_queryset().filter(username=username).exists()


def check_user_exists_by_email(email: str) -> bool:
    return base_user_queryset().filter(email=email).exists()


def get_user_by_id(user_id: UUID):
    return base_user_queryset().filter(id=user_id).first()


def get_user_with_profile(user_id: UUID):
    return base_user_queryset().select_related("profile").filter(id=user_id).first()


def verify_password(user, password: str) -> bool:
    return user.check_password(password)


def is_nickname_taken(nickname: str, exclude_user_id: Optional[UUID] = None) -> bool:
    qs = UserProfile.objects.filter(nickname=nickname, is_deleted=False)
    if exclude_user_id:
        qs = qs.exclude(user_id=exclude_user_id)
    return qs.exists()


def get_user_activities(user, activity_type: Optional[str] = None) -> QuerySet:
    qs = UserActivity.objects.filter(user=user, is_deleted=False).order_by("-created_at")
    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    return qs


def paginate_queryset(qs: QuerySet, page: int, page_size: int) -> Tuple[list, int, int]:
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)
    return list(page_obj.object_list), paginator.count, paginator.num_pages


def filter_users(search: Optional[str] = None) -> QuerySet:
    qs = base_user_queryset().select_related("profile").order_by("-created_at")
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(profile__nickname__icontains=search)
        )
    return qs


def get_admin_dashboard_metrics() -> dict:
    today = timezone.now().date()
    total_users = base_user_queryset().count()
    staff_users = base_user_queryset().filter(is_staff=True).count()
    active_users = base_user_queryset().filter(is_active=True).count()
    new_users_today = base_user_queryset().filter(created_at__date=today).count()
    activities_today = UserActivity.objects.filter(created_at__date=today, is_deleted=False).count()
    logins_today = UserActivity.objects.filter(
        activity_type="login", created_at__date=today, is_deleted=False
    ).count()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "staff_users": staff_users,
        "regular_users": total_users - staff_users,
        "new_users_today": new_users_today,
        "activities_today": activities_today,
        "logins_today": logins_today,
    }


def get_dashboard_chart_series(days: int = 30) -> dict:
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    registration_qs = (
        base_user_queryset()
        .filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
    )
    registration_map = {item["day"]: item["count"] for item in registration_qs}

    activity_qs = (
        UserActivity.objects.filter(
            activity_type="login",
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            is_deleted=False,
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
    )
    activity_map = {item["day"]: item["count"] for item in activity_qs}

    registration_dates = []
    registration_counts = []
    activity_dates = []
    activity_counts = []
    total_users_by_date = []

    base_total = base_user_queryset().filter(created_at__date__lt=start_date).count()
    running_total = base_total

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        reg_count = registration_map.get(current_date, 0)
        registration_dates.append(date_str)
        registration_counts.append(reg_count)

        act_count = activity_map.get(current_date, 0)
        activity_dates.append(date_str)
        activity_counts.append(act_count)

        running_total += reg_count
        total_users_by_date.append({"date": date_str, "count": running_total})

        current_date += timedelta(days=1)

    return {
        "registration": {"dates": registration_dates, "counts": registration_counts},
        "activity": {"dates": activity_dates, "counts": activity_counts},
        "total_users": {"data": total_users_by_date},
    }


import plotly.graph_objects as go
import json

def get_dashboard_plotly_data(days: int = 30) -> dict:
    """使用 Plotly 生成仪表盘图表数据。"""
    series_data = get_dashboard_chart_series(days=days)
    
    # 注册趋势图
    fig = go.Figure()
    
    # 添加新增用户线
    fig.add_trace(go.Scatter(
        x=series_data["registration"]["dates"],
        y=series_data["registration"]["counts"],
        name="新增用户",
        mode='lines+markers',
        line=dict(color='#ea580c', width=3, shape='spline'),
        marker=dict(size=6, color='#ea580c'),
        fill='tozeroy',
        fillcolor='rgba(234, 88, 12, 0.1)',
        hovertemplate='日期: %{x}<br>新增用户: %{y}<extra></extra>'
    ))

    # 布局配置
    fig.update_layout(
        margin=dict(t=10, b=40, l=40, r=10),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hovermode='closest',
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10),
            color='#94a3b8'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickfont=dict(size=10),
            color='#94a3b8',
            zeroline=False
        )
    )

    # 转换成字典格式，直接供前端 Plotly.js 使用
    return fig.to_dict()


def serialize_user(user) -> dict:
    profile = getattr(user, "profile", None)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "date_joined": to_iso(getattr(user, "date_joined", None)),
        "last_login": to_iso(getattr(user, "last_login", None)),
        "created_at": to_iso(getattr(user, "created_at", None)),
        "updated_at": to_iso(getattr(user, "updated_at", None)),
        "profile": {
            "nickname": getattr(profile, "nickname", None),
            "phone": getattr(profile, "phone", None),
            "gender": getattr(profile, "gender", None),
            "birth_date": to_iso(getattr(profile, "birth_date", None)),
            "status": getattr(profile, "status", None),
            "login_count": getattr(profile, "login_count", 0),
            "last_activity": to_iso(getattr(profile, "last_activity", None)),
            "avatar": profile.avatar.url if profile and profile.avatar else None,
        }
        if profile
        else None,
    }


__all__ = [
    "authenticate_user",
    "check_user_exists_by_email",
    "check_user_exists_by_username",
    "get_user_by_id",
    "get_user_with_profile",
    "verify_password",
    "is_nickname_taken",
    "get_user_activities",
    "paginate_queryset",
    "filter_users",
    "get_admin_dashboard_metrics",
    "get_dashboard_chart_series",
    "get_dashboard_plotly_data",
    "serialize_user",
    "Role",
    "UserActivity",
    "UserProfile",
    "User",
]
