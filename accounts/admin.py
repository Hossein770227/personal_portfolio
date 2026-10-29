
import jdatetime

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import MyUser, OtpCode
from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm as UnfoldUserChangeForm,
    UserCreationForm as UnfoldUserCreationForm,
)

@admin.register(MyUser)
class MyUserAdmin(BaseUserAdmin,ModelAdmin):
    form = UnfoldUserChangeForm
    add_form = UnfoldUserCreationForm
    change_password_form = AdminPasswordChangeForm


    list_display = (
        "full_name",
        "phone_number",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_display_links = ("full_name", "phone_number")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("full_name", "phone_number")
    ordering = ("full_name",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {
            "fields": ("phone_number", "full_name", "password"),
        }),
        (_("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        (_("Important dates"), {
            "fields": ("last_login",),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "full_name",
                "password1",
                "password2",
                "is_active",
                "is_staff",
            ),
        }),
    )

    readonly_fields = ("last_login",)


@admin.register(OtpCode)
class OtpCodeAdmin(ModelAdmin):
    list_display = (
        "phone_number",
        "date_time_persian",
        "expire_time",
        "expiration_status",
    )

    list_filter = ("date_time_created", "expire_time")
    search_fields = ("phone_number",)
    ordering = ("-date_time_created",)

    readonly_fields = (
        "phone_number",
        "code",
        "date_time_created",
        "expire_time",
    )

    fields = (
        "phone_number",
        "code",
        "date_time_created",
        "expire_time",
    )

    @admin.display(description=_("Date/Time (Persian)"))
    def date_time_persian(self, obj):
        if not obj.date_time_created:
            return "-"

        return jdatetime.datetime.fromgregorian(
            datetime=obj.date_time_created
        ).strftime("%Y/%m/%d %H:%M:%S")
    
    @admin.display(description=_("Expired"), boolean=True)
    def expiration_status(self, obj):
        return timezone.now() >= obj.expire_time
    
    # @admin.display(description=_("OTP status"))
    # def expiration_status(self, obj):
    #     if timezone.now() >= obj.expire_time:
    #         return _("Expired")

    #     return _("Valid")
