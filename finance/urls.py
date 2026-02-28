from django.urls import path

from .views import (
    BonusCreateView,
    DeductionCreateView,
    InvoiceCreateView,
    InvoiceListView,
    PaymentCreateView,
    PaymentListView,
    PayrollApproveView,
    PayrollDetailView,
    PayrollGenerateView,
    PayrollListView,
    PayrollPayView,
)

urlpatterns = [
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),

    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),

    path('payroll/', PayrollListView.as_view(), name='payroll-list'),
    path('payroll/<int:pk>/', PayrollDetailView.as_view(), name='payroll-detail'),
    path('payroll/generate/', PayrollGenerateView.as_view(), name='payroll-generate'),
    path('payroll/approve/<int:pk>/', PayrollApproveView.as_view(), name='payroll-approve'),
    path('payroll/pay/<int:pk>/', PayrollPayView.as_view(), name='payroll-pay'),

    path('bonus/create/', BonusCreateView.as_view(), name='bonus-create'),
    path('deduction/create/', DeductionCreateView.as_view(), name='deduction-create'),
]
