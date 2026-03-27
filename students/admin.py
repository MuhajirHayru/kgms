from django.contrib import admin
from .models import (
    GradeCapacitySetting,
    Invoice,
    Parent,
    ParentNotification,
    Payment,
    PenaltySetting,
    Student,
    StudentCertificate,
    StudentFeeSetting,
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'category', 'grade_level', 'class_name', 'transport', 'dob',
        'parent', 'monthly_tuition_fee', 'registration_fee', 'transport_fee', 'active'
    )
    list_filter = ('category', 'grade_level', 'class_name', 'transport', 'active')
    search_fields = ('first_name', 'last_name', 'parent__full_name', 'parent__phone_number', 'grade_level', 'class_name')


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number')
    search_fields = ('full_name', 'phone_number')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'amount', 'penalty_amount', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'month')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'paid_at', 'paid_by')
    search_fields = ('invoice__student__first_name', 'invoice__student__last_name')


@admin.register(StudentCertificate)
class StudentCertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'file', 'uploaded_at')
    search_fields = ('student__first_name', 'student__last_name')


@admin.register(PenaltySetting)
class PenaltySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'penalty_per_day', 'updated_at')


@admin.register(StudentFeeSetting)
class StudentFeeSettingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'kg_monthly_fee',
        'elementary_monthly_fee',
        'registration_fee',
        'bus_transport_fee',
        'updated_at',
    )


@admin.register(GradeCapacitySetting)
class GradeCapacitySettingAdmin(admin.ModelAdmin):
    list_display = ('grade_level', 'max_students_per_section', 'updated_at')
    search_fields = ('grade_level',)


@admin.register(ParentNotification)
class ParentNotificationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'notification_type', 'sent_at')
    list_filter = ('notification_type',)
    search_fields = ('parent__full_name', 'parent__phone_number', 'student__first_name', 'student__last_name')
