from django.urls import path
from .views import (
    StudentListCreateView,
    StudentDetailView,
    ParentListCreateView,
    ParentDetailView,
    InvoiceListCreateView,
    PaymentListCreateView
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
]
