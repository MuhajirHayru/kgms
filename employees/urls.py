from django.urls import path
from .views import EmployeeCreateView, AttendanceCreateView

urlpatterns = [
    path('create/', EmployeeCreateView.as_view(), name='employee-create'),
    path('attendance/', AttendanceCreateView.as_view(), name='attendance-create'),
]