from django.urls import path
from .views import *
    

urlpatterns = [
    # Employee management
    path('register/', EmployeeRegisterView.as_view(), name='employee-register'),  # Director registration API
    path('employees/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('', EmployeeListView.as_view(),name='employeelist'),
    # Attendance management
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/create/', AttendanceCreateView.as_view(), name='attendance-create'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
    path('attendance/update/<int:pk>/', AttendanceUpdateView.as_view(), name='attendance-update'),
]