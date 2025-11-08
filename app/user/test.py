"""
User微服务测试模块
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser
import json

# 导入API模块
from app.user.api import login_user, register_user, logout_user, get_user_profile, change_password, admin_dashboard, list_users
# 导入验证器
from app.utils.validators import UserLoginSchema, UserRegisterSchema, UserUpdateSchema, ChangePasswordSchema


class UserApiTestCase(TestCase):
    """用户API测试用例"""
    
    def setUp(self):
        """测试初始化"""
        self.factory = RequestFactory()
        try:
            self.admin_user = User.objects.create_user(
                username='admin', 
                email='admin@example.com', 
                password='admin123456', 
                is_staff=True
            )
            self.regular_user = User.objects.create_user(
                username='user', 
                email='user@example.com', 
                password='user123456'
            )
        except Exception as e:
            self.fail(f"Failed to create test users: {e}")

    def test_user_registration(self):
        """测试用户注册"""
        # 创建模拟请求
        request = self.factory.post('/api/auth/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'newpass123',
                'password2': 'newpass123',
                'captcha': 'test',
                'captcha_key': 'test'
            }),
            content_type='application/json'
        )
        
        # 创建测试数据
        data = UserRegisterSchema(
            username='newuser',
            email='new@example.com',
            password1='newpass123',
            password2='newpass123',
            captcha='test',
            captcha_key='test'
        )
        
        response = register_user(request, data)
        self.assertEqual(response.status_code, 201)

    def test_user_login_success(self):
        """测试用户登录成功"""
        request = self.factory.post('/api/auth/login',
            data=json.dumps({
                'username': 'user',
                'password': 'user123456'
            }),
            content_type='application/json'
        )
        
        # 模拟session中间件
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        
        data = UserLoginSchema(username='user', password='user123456')
        response = login_user(request, data)
        self.assertEqual(response.status_code, 200)

    def test_user_login_invalid_credentials(self):
        """测试用户登录失败"""
        request = self.factory.post('/api/auth/login',
            data=json.dumps({
                'username': 'user',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        data = UserLoginSchema(username='user', password='wrongpassword')
        response = login_user(request, data)
        self.assertEqual(response.status_code, 400)

    def test_user_logout(self):
        """测试用户登出"""
        # 创建登出请求并设置用户
        logout_request = self.factory.post('/api/auth/logout')
        logout_request.user = self.regular_user
        
        # 模拟session
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(logout_request)
        
        response = logout_user(logout_request)
        self.assertEqual(response.status_code, 200)

    def test_get_user_profile_unauthenticated(self):
        """测试获取未认证用户信息"""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/api/user/profile')
        request.user = AnonymousUser()
        response = get_user_profile(request)
        self.assertEqual(response.status_code, 401)

    def test_get_user_profile_authenticated(self):
        """测试获取已认证用户信息"""
        request = self.factory.get('/api/user/profile')
        request.user = self.regular_user
        response = get_user_profile(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_no_permission(self):
        """测试无权限访问管理后台"""
        request = self.factory.get('/api/admin/dashboard')
        request.user = self.regular_user
        response = admin_dashboard(request)
        self.assertEqual(response.status_code, 403)

    def test_list_users_no_permission(self):
        """测试无权限查看用户列表"""
        request = self.factory.get('/api/admin/users')
        request.user = self.regular_user
        response = list_users(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_access(self):
        """测试管理员访问管理后台"""
        request = self.factory.get('/api/admin/dashboard')
        request.user = self.admin_user
        response = admin_dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_list_users_admin(self):
        """测试管理员查看用户列表"""
        request = self.factory.get('/api/admin/users')
        request.user = self.admin_user
        response = list_users(request)
        self.assertEqual(response.status_code, 200)


class UserModelTestCase(TestCase):
    """用户模型测试用例"""
    
    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """测试创建超级用户"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(superuser.username, 'admin')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class UserPermissionsTestCase(TestCase):
    """用户权限测试用例"""
    
    def setUp(self):
        """测试初始化"""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            username='admin_user', 
            email='admin@example.com', 
            password='admin123', 
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', 
            email='user@example.com', 
            password='user123'
        )

    def test_admin_can_view_all_users(self):
        """测试管理员可以查看所有用户"""
        request = self.factory.get('/api/admin/users')
        request.user = self.admin_user
        response = list_users(request)
        self.assertEqual(response.status_code, 200)

    def test_user_can_view_own_profile(self):
        """测试用户可以查看自己的信息"""
        request = self.factory.get('/api/user/profile')
        request.user = self.regular_user
        response = get_user_profile(request)
        self.assertEqual(response.status_code, 200)