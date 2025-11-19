"""
用户新增功能API接口
包含3个接口：上传头像、获取活动记录、更新个人资料
"""

from .base import BaseUserAPI, success_response, error_response
from app.user.schemas import UserProfileUpdateSchema
from app.user.models import UserActivity,UserProfile
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from app.utils.log_utils import log_user_action
from app.log.model import Log

class UserFeatureAPI(BaseUserAPI):
    """用户新增功能API"""
    
    def _setup_routes(self):
        @self.router.post("/user/upload-avatar")
        def upload_avatar(request):
            return self._upload_avatar(request)
        
        @self.router.get("/user/activities")
        def get_user_activities(request, page: int = 1, page_size: int = 10, activity_type=None):
            return self._get_user_activities(request, page, page_size, activity_type)
        
        @self.router.post("/user/update-profile")
        def update_profile(request, data: UserProfileUpdateSchema):
            return self._update_profile(request, data)
    
    def _upload_avatar(self, request):
        """上传用户头像"""
        try:
            # 检查认证
            auth_check = self.check_authentication(request)
            if auth_check:
                return auth_check
            
            user = request.user
            profile = user.profile if hasattr(user, 'profile') else None
            
            if not profile:
                log_user_action(
                    action="上传头像",
                    message=f"用户 {user.username} 上传头像失败：用户资料不存在",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request
                )
                return error_response(
                    message="用户资料不存在",
                    status_code=404
                )
            
            # 获取上传的文件
            if not hasattr(request, 'FILES') or 'file' not in request.FILES:
                log_user_action(
                    action="上传头像",
                    message=f"用户 {user.username} 上传头像失败：未提供文件",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request
                )
                return error_response(
                    message="未提供文件",
                    status_code=400
                )
            
            file = request.FILES['file']
            
            # 验证文件类型
            if not file.content_type.startswith('image/'):
                log_user_action(
                    action="上传头像",
                    message=f"用户 {user.username} 上传头像失败：只能上传图片文件",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"file_type": file.content_type}
                )
                return error_response(
                    message="只能上传图片文件",
                    status_code=400
                )
            
            # 验证文件大小 (5MB限制)
            if file.size > 5 * 1024 * 1024:
                log_user_action(
                    action="上传头像",
                    message=f"用户 {user.username} 上传头像失败：文件大小超过5MB",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"file_size": file.size}
                )
                return error_response(
                    message="文件大小不能超过5MB",
                    status_code=400
                )
            
            # 删除旧头像
            if profile.avatar:
                profile.delete_avatar()
            
            # 保存新头像
            profile.avatar = file
            profile.save()
            
            # 记录活动
            try:
                UserActivity.objects.create(
                    user=user,
                    activity_type='avatar_upload',
                    description=f'用户 {user.username} 更新了头像',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass  # 活动记录失败不影响主流程
            
            # 记录上传头像成功日志
            log_user_action(
                action="上传头像",
                message=f"用户 {user.username} 上传头像成功",
                user=user,
                request=request,
                extra_data={
                    "file_size": file.size,
                    "file_type": file.content_type
                }
            )
            
            return success_response(
                data={
                    'avatar_url': profile.avatar.url if profile.avatar else None,
                },
                message="头像上传成功"
            )
            
        except Exception as exc:
            # 记录上传头像异常日志
            log_user_action(
                action="上传头像",
                message=f"用户 {request.user.username} 上传头像异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"error": str(exc)}
            )
            return error_response(
                message=f"头像上传失败: {str(exc)}",
                status_code=500
            )
    
    def _get_user_activities(self, request, page: int = 1, page_size: int = 10, activity_type=None):
        """获取用户活动记录"""
        try:
            # 检查认证
            auth_check = self.check_authentication(request)
            if auth_check:
                return auth_check
            
            user = request.user
            activities_query = UserActivity.objects.filter(user=user)
            
            if activity_type:
                activities_query = activities_query.filter(activity_type=activity_type)
            
            # 分页
            paginator = Paginator(activities_query.order_by('-created'), page_size)
            activities_page = paginator.get_page(page)
            
            # 转换为字典列表
            activities_data = []
            for activity in activities_page:
                activities_data.append({
                    'id': activity.id,
                    'activity_type': activity.get_activity_type_display(),
                    'description': activity.description,
                    'ip_address': activity.ip_address,
                    'created_at': activity.created.strftime('%Y-%m-%d %H:%M:%S'),
                })
            
            return success_response(
                data={
                    'activities': activities_data,
                    'page': page,
                    'page_size': page_size,
                    'total_count': paginator.count,
                    'total_pages': paginator.num_pages
                },
                message="获取活动记录成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取活动记录失败: {str(exc)}",
                status_code=500
            )
    
    def _update_profile(self, request, data: UserProfileUpdateSchema):
        """更新用户个人资料"""
        try:
            # 检查认证
            auth_check = self.check_authentication(request)
            if auth_check:
                return auth_check
            
            user = request.user
            profile = user.profile if hasattr(user, 'profile') else None
            
            if not profile:
                log_user_action(
                    action="更新个人资料",
                    message=f"用户 {user.username} 更新个人资料失败：用户资料不存在",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request
                )
                return error_response(
                    message="用户资料不存在",
                    status_code=404
                )
            
            # 更新字段
            if data.phone is not None:
                profile.phone = data.phone
            
            if data.nickname is not None:
                nickname_value = data.nickname
                if nickname_value and nickname_value.strip():
                    # 检查昵称唯一性（排除当前用户）
                    existing_profile = UserProfile.objects.filter(
                        nickname=nickname_value.strip()
                    ).exclude(pk=profile.pk).first()
                    if existing_profile:
                        log_user_action(
                            action="更新个人资料",
                            message=f"用户 {user.username} 更新个人资料失败：昵称已被其他用户使用",
                            level=Log.LEVEL.WARNING,
                            user=user,
                            request=request,
                            extra_data={"nickname": nickname_value.strip(), "reason": "昵称已被使用"}
                        )
                        return error_response(
                                message="昵称已被其他用户使用，请选择其他昵称",
                            status_code=400
                        )
                    profile.nickname = nickname_value.strip()
                else:
                    # 空昵称会触发自动生成
                    profile.nickname = None
            
            if data.gender is not None:
                profile.gender = data.gender
            
            if data.birth_date is not None:
                profile.birth_date = data.birth_date
            
            profile.save()
            
            # 记录活动
            try:
                UserActivity.objects.create(
                    user=user,
                    activity_type='profile_update',
                    description=f'用户 {user.username} 更新了个人资料',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass  # 活动记录失败不影响主流程
            
            # 记录更新个人资料成功日志
            log_user_action(
                action="更新个人资料",
                message=f"用户 {user.username} 更新个人资料成功",
                user=user,
                request=request,
                extra_data={
                    "updated_fields": {
                        "phone": data.phone is not None,
                        "nickname": data.nickname is not None,
                        "gender": data.gender is not None,
                        "birth_date": data.birth_date is not None
                    }
                }
            )
            
            return success_response(
                data={
                    'phone': profile.phone,
                    'nickname': profile.nickname,
                    'gender': profile.gender,
                    'birth_date': profile.birth_date.strftime('%Y-%m-%d') if profile.birth_date else None,
                },
                message="个人资料更新成功"
            )
            
        except Exception as exc:
            # 记录更新个人资料异常日志
            log_user_action(
                action="更新个人资料",
                message=f"用户 {request.user.username} 更新个人资料异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"error": str(exc)}
            )
            return error_response(
                message=f"个人资料更新失败: {str(exc)}",
                status_code=500
            )
