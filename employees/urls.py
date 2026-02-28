from django.urls import path
from .views import (
    ChangePasswordView,
    EmployeeRegisterView,
    EmployeeListView,
    AttendanceListView,
    AttendanceCreateView,
    AttendanceDetailView,
    AttendanceUpdateView,
)

urlpatterns = [
    # Employee management
    path('register/', EmployeeRegisterView.as_view(), name='employee-register'),  # Director registration API
    path('list/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Attendance management
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/create/', AttendanceCreateView.as_view(), name='attendance-create'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
    path('attendance/update/<int:pk>/', AttendanceUpdateView.as_view(), name='attendance-update'),
]