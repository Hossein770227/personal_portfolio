from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import MyUserManager
from .validator import validate_iranian_phone




class MyUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        verbose_name=_("phone number"),
        max_length=13,
        unique=True,
        db_index=True,
        validators=[validate_iranian_phone],
    )
    full_name = models.CharField(
        verbose_name=_("full name"),
        max_length=100,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    @classmethod
    def get_by_phone(cls, phone_number):
        return cls.objects.filter(phone_number=phone_number).first()


def get_expire_time():
    return timezone.now() + timedelta(minutes=2)


class OtpCode(models.Model):
    phone_number = models.CharField(
        verbose_name="phone number",
        max_length=13,
        db_index=True,
        validators=[validate_iranian_phone],
    )
    code = models.CharField(
        verbose_name="verification code",
        max_length=6,
    )
    date_time_created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    expire_time = models.DateTimeField(
        default=get_expire_time,
        db_index=True,
    )

    class Meta:
        verbose_name = _("otp code")
        verbose_name_plural = _("otp codes")
        ordering = ["-date_time_created"]
        indexes = [
            models.Index(fields=["phone_number", "code"]),
        ]

    def __str__(self):
        return f"{self.phone_number}: {self.code}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expire_time

    @classmethod
    def delete_expired(cls):
        cls.objects.filter(expire_time__lt=timezone.now()).delete()

