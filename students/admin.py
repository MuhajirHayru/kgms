from django.contrib import admin
from .models import Student, Parent, Invoice, Payment

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'dob', 'parent', 'active')
    search_fields = ('first_name', 'last_name', 'parent__first_name', 'parent__last_name')


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'amount', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'month')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'paid_at', 'paid_by')
    search_fields = ('invoice__student__first_name', 'invoice__student__last_name')