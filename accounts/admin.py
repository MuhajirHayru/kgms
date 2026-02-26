from django.contrib import admin

from .models import DriverProfile, ParentProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "phone_number",
        "full_name",
        "role",
        "must_change_password",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("phone_number", "full_name")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "must_change_password")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_phone_number",
        "user_full_name",
        "occupation",
        "relationship_to_student",
        "password_hash",
    )
    search_fields = ("user__phone_number", "full_name", "occupation")
    list_filter = ("relationship_to_student",)

    @admin.display(ordering="user__phone_number", description="phone_number")
    def user_phone_number(self, obj):
        return obj.user.phone_number

    @admin.display(ordering="full_name", description="full_name")
    def user_full_name(self, obj):
        return obj.full_name

    @admin.display(ordering="user__password", description="password(hash)")
    def password_hash(self, obj):
        return obj.user.password


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user_phone_number", "license_number")
    search_fields = ("user__phone_number", "license_number")

    @admin.display(ordering="user__phone_number", description="phone_number")
    def user_phone_number(self, obj):
        return obj.user.phone_number
