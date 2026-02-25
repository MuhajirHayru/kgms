from django.urls import path
from .views import ParentRegisterView, ParentChangePasswordView

urlpatterns = [
    path('parents/register/', ParentRegisterView.as_view(), name='parent-register'),
    path('parents/change-password/', ParentChangePasswordView.as_view(), name='parent-change-password'),
]