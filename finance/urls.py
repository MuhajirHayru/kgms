from django.urls import path
from .views import InvoiceCreateView, PaymentCreateView
from django.urls import path
from .views import (
    PayrollListView,
    PayrollDetailView,
    PayrollGenerateView,
    PayrollApproveView,
    PayrollPayView
)

urlpatterns = [
    path('invoices/', InvoiceCreateView.as_view(), name='invoice-create'),
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),


    path('payroll/', PayrollListView.as_view(), name='payroll-list'),
    path('payroll/<int:pk>/', PayrollDetailView.as_view(), name='payroll-detail'),
    path('payroll/generate/', PayrollGenerateView.as_view(), name='payroll-generate'),
    path('payroll/approve/<int:pk>/', PayrollApproveView.as_view(), name='payroll-approve'),
    path('payroll/pay/<int:pk>/', PayrollPayView.as_view(), name='payroll-pay'),

]

