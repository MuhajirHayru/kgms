from django.urls import path
from .views import (
    AdminResetUserPasswordView,
    ParentChangePasswordView,
    ParentListView,
    ParentRegisterView,
)

urlpatterns = [
    path('parents/list/', ParentListView.as_view(), name='parent-list'),
    path('parents/register/', ParentRegisterView.as_view(), name='parent-register'),
    path('parents/change-password/', ParentChangePasswordView.as_view(), name='parent-change-password'),
    path('admin/reset-password/', AdminResetUserPasswordView.as_view(), name='admin-reset-password'),
]