from django.contrib import admin
from .models import Student, Parent, Invoice, Payment, StudentCertificate

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'dob', 'parent', 'active', 'student_photo')
    search_fields = ('first_name', 'last_name', 'parent__full_name', 'parent__phone_number')


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'amount', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'month')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'paid_at', 'paid_by')
    search_fields = ('invoice__student__first_name', 'invoice__student__last_name')


@admin.register(StudentCertificate)
class StudentCertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'file', 'uploaded_at')
    search_fields = ('student__first_name', 'student__last_name')
