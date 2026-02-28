from django.urls import path

from .views import (
    BonusCreateView,
    CreditGiveView,
    CreditRepaymentCreateView,
    CreditRequestCreateView,
    CreditRequestListView,
    CreditReviewView,
    DashboardNotificationListView,
    DeductionCreateView,
    EmployeeSalaryUpdateView,
    ExpenseMarkPaidView,
    ExpenseRequestCreateView,
    ExpenseRequestListView,
    ExpenseReviewView,
    HideDashboardNotificationsView,
    InvoiceCreateView,
    InvoiceListView,
    LedgerEntryListView,
    ManualIncomeCreateView,
    MonthlyReportView,
    PaymentCreateView,
    PaymentListView,
    PayrollDetailView,
    PayrollGenerateView,
    PayrollListView,
    PayrollPayView,
    PayrollRequestPaymentView,
    PayrollReviewView,
    SchoolAccountInitializeView,
    SchoolAccountView,
    PayrollSettingView,
)

urlpatterns = [
    path('account/', SchoolAccountView.as_view(), name='school-account'),
    path('account/initialize/', SchoolAccountInitializeView.as_view(), name='school-account-initialize'),
    path('ledger/', LedgerEntryListView.as_view(), name='ledger-list'),
    path('income/manual/', ManualIncomeCreateView.as_view(), name='manual-income-create'),
    path('reports/monthly/', MonthlyReportView.as_view(), name='monthly-report'),

    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),

    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),

    path('payroll/', PayrollListView.as_view(), name='payroll-list'),
    path('payroll/<int:pk>/', PayrollDetailView.as_view(), name='payroll-detail'),
    path('payroll/generate/', PayrollGenerateView.as_view(), name='payroll-generate'),
    path('payroll/request-payment/', PayrollRequestPaymentView.as_view(), name='payroll-request-payment'),
    path('payroll/review/<int:pk>/', PayrollReviewView.as_view(), name='payroll-review'),
    path('payroll/pay/<int:pk>/', PayrollPayView.as_view(), name='payroll-pay'),

    path('bonus/create/', BonusCreateView.as_view(), name='bonus-create'),
    path('deduction/create/', DeductionCreateView.as_view(), name='deduction-create'),

    path('expenses/', ExpenseRequestListView.as_view(), name='expense-list'),
    path('expenses/create/', ExpenseRequestCreateView.as_view(), name='expense-create'),
    path('expenses/review/<int:pk>/', ExpenseReviewView.as_view(), name='expense-review'),
    path('expenses/pay/<int:pk>/', ExpenseMarkPaidView.as_view(), name='expense-pay'),

    path('credits/', CreditRequestListView.as_view(), name='credit-list'),
    path('credits/create/', CreditRequestCreateView.as_view(), name='credit-create'),
    path('credits/review/<int:pk>/', CreditReviewView.as_view(), name='credit-review'),
    path('credits/give/<int:pk>/', CreditGiveView.as_view(), name='credit-give'),
    path('credits/repayments/create/', CreditRepaymentCreateView.as_view(), name='credit-repayment-create'),

    path('payroll/settings/', PayrollSettingView.as_view(), name='payroll-settings'),
    path('employees/salary/', EmployeeSalaryUpdateView.as_view(), name='employee-salary-update'),
    path('notifications/', DashboardNotificationListView.as_view(), name='dashboard-notifications'),
    path('notifications/hide/', HideDashboardNotificationsView.as_view(), name='dashboard-notifications-hide'),
]
