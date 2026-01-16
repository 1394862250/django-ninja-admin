"""Django models module wrapper for auto-discovery."""
from .model import DocumentUpload, Role, User, UserActivity, UserProfile, UserRole

__all__ = ["User", "UserProfile", "UserActivity", "DocumentUpload", "Role", "UserRole"]
