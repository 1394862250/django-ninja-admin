"""
用户新增功能API接口
包含3个接口：上传头像、获取活动记录、更新个人资料
"""
from ninja import Router
from django.core.paginator import Paginator
from datetime import datetime

from .user_feature_schemas import UserProfileUpdateSchema
from app.user.models import UserActivity, UserProfile
from app.user.flows.user_flow import upload_avatar_flow, update_profile_flow, get_user_activities_flow
from app.utils.log_utils import log_user_action
from app.log.model import Log
from app.utils.responses import success_response, error_response


def create_user_feature_api_router():
    """创建用户功能API路由"""
    router = Router()

    @router.post("/user/upload-avatar")
    def upload_avatar(request):
        """上传用户头像"""
        # 权限检查：必须已登录
        if not request.user.is_authenticated:
            return error_response(message="需要登录访问", status_code=401)

        # 获取上传的文件
        if not hasattr(request, 'FILES') or 'file' not in request.FILES:
            log_user_action(
                action="上传头像",
                message=f"用户 {request.user.username} 上传头像失败：未提供文件",
                level=Log.LEVEL.WARNING,
                user=request.user,
                request=request
            )
            return error_response(message="未提供文件", status_code=400)

        file = request.FILES['file']

        # 验证文件类型
        if not file.content_type.startswith('image/'):
            log_user_action(
                action="上传头像",
                message=f"用户 {request.user.username} 上传头像失败：只能上传图片文件",
                level=Log.LEVEL.WARNING,
                user=request.user,
                request=request,
                extra_data={"file_type": file.content_type}
            )
            return error_response(message="只能上传图片文件", status_code=400)

        # 验证文件大小 (5MB限制)
        if file.size > 5 * 1024 * 1024:
            log_user_action(
                action="上传头像",
                message=f"用户 {request.user.username} 上传头像失败：文件大小超过5MB",
                level=Log.LEVEL.WARNING,
                user=request.user,
                request=request,
                extra_data={"file_size": file.size}
            )
            return error_response(message="文件大小不能超过5MB", status_code=400)

        # 调用 Flow
        result = upload_avatar_flow(request, file)

        if not result.success:
            return error_response(message=result.message, status_code=500)

        return success_response(
            data={'avatar_url': result.avatar_url},
            message=result.message
        )

    @router.get("/user/activities")
    def get_user_activities(request, page: int = 1, page_size: int = 10, activity_type=None):
        """获取用户活动记录"""
        # 调用 Flow
        result = get_user_activities_flow(
            request=request,
            page=page,
            page_size=page_size,
            activity_type=activity_type
        )

        if not result.success:
            return error_response(message=result.message, status_code=401)

        return success_response(data=result.data, message=result.message)

    @router.post("/user/update-profile")
    def update_profile(request, data: UserProfileUpdateSchema):
        """更新用户个人资料"""
        # 调用 Flow(权限检查在 Flow 中)
        result = update_profile_flow(
            request=request,
            nickname=data.nickname,
            gender=data.gender,
            birth_date=data.birth_date,
            phone=data.phone
        )

        if not result.success:
            return error_response(message=result.message, status_code=400)

        # 获取更新后的资料
        profile = request.user.profile
        return success_response(
            data={
                'phone': profile.phone,
                'nickname': profile.nickname,
                'gender': profile.gender,
                'birth_date': profile.birth_date.strftime('%Y-%m-%d') if profile.birth_date else None,
            },
            message=result.message
        )

    return router
