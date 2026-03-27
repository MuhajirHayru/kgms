from django.urls import path
from .views import (
    AccountantMonthlyDashboardView,
    AccountantMonthlyFeesView,
    GenerateCurrentMonthInvoicesView,
    ParentNotificationListView,
    StudentListCreateView,
    StudentDetailView,
    ParentListCreateView,
    ParentDetailView,
    InvoiceListCreateView,
    PaymentListCreateView,
    PenaltySettingView,
    ReminderRunView,
    StudentFeeSettingView,
)

urlpatterns = [
    # Students
    path('students/', StudentListCreateView.as_view(), name='student-list-create'),
    path('students/<int:pk>/', StudentDetailView.as_view(), name='student-detail'),

    # Parents
    path('parents/', ParentListCreateView.as_view(), name='parent-list-create'),
    path('parents/<int:pk>/', ParentDetailView.as_view(), name='parent-detail'),

    # Finance
    path('invoices/', InvoiceListCreateView.as_view(), name='invoice-create'),
    path('payments/', PaymentListCreateView.as_view(), name='payment-create'),
    path('fees/generate-current-month/', GenerateCurrentMonthInvoicesView.as_view(), name='fees-generate-current'),
    path('fees/dashboard/', AccountantMonthlyDashboardView.as_view(), name='fees-dashboard'),
    path('fees/monthly/', AccountantMonthlyFeesView.as_view(), name='fees-monthly'),
    path('fees/penalty-setting/', PenaltySettingView.as_view(), name='fees-penalty-setting'),
    path('fees/settings/', StudentFeeSettingView.as_view(), name='student-fee-setting'),
    path('fees/run-reminders/', ReminderRunView.as_view(), name='fees-run-reminders'),
    path('parents/notifications/', ParentNotificationListView.as_view(), name='parent-notifications'),
]
