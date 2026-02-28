from django.contrib import admin
from .models import (
    Bonus,
    CreditRepayment,
    CreditRequest,
    DashboardNotification,
    Deduction,
    ExpenseRequest,
    Invoice,
    LedgerEntry,
    Payment,
    Payroll,
    PayrollSetting,
    SchoolAccount,
)


@admin.register(PayrollSetting)
class PayrollSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'tax_rate_percent', 'updated_at')


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'month', 'base_salary', 'total_present_days',
        'gross_salary', 'tax_rate_percent', 'tax_amount', 'net_salary', 'status'
    )
    list_filter = ('status', 'month')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('parent', 'month', 'amount', 'is_paid', 'due_date')
    list_filter = ('is_paid', 'month')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'paid_amount', 'paid_at', 'paid_by')


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'amount', 'reason')


@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'amount', 'reason')


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'category', 'title', 'is_read', 'is_hidden', 'created_at')
    list_filter = ('category', 'is_read', 'is_hidden')


@admin.register(SchoolAccount)
class SchoolAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_balance', 'is_initialized', 'updated_at')


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_type', 'amount_delta', 'created_by', 'created_at')
    list_filter = ('entry_type',)


@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'status', 'requested_by', 'created_at')
    list_filter = ('status', 'category')


@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'status', 'total_repaid', 'created_at')
    list_filter = ('status',)


@admin.register(CreditRepayment)
class CreditRepaymentAdmin(admin.ModelAdmin):
    list_display = ('credit_request', 'amount', 'recorded_by', 'created_at')
