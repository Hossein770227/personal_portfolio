
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import MyUserManager
from .validator import validate_iranian_phone


def get_expire_time():
    return timezone.now() + timedelta(minutes=2)


class MyUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        verbose_name=_("phone number"),
        max_length=13,
        unique=True,
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


class OtpCode(models.Model):
    class Purpose(models.TextChoices):
        REGISTRATION = "registration", _("Registration")
        PASSWORD_RESET = "password_reset", _("Password reset")

    phone_number = models.CharField(
        verbose_name=_("phone number"),
        max_length=13,
        validators=[validate_iranian_phone],
    )

    code = models.CharField(
        verbose_name=_("verification code hash"),
        max_length=128,
    )

    purpose = models.CharField(
        verbose_name=_("purpose"),
        max_length=20,
        choices=Purpose.choices,
        db_index=True,
    )

    attempts = models.PositiveSmallIntegerField(default=0)

    date_time_created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    expire_time = models.DateTimeField(
        default=get_expire_time,
        db_index=True,
    )

    class Meta:
        verbose_name = _("OTP code")
        verbose_name_plural = _("OTP codes")
        ordering = ["-date_time_created"]
        indexes = [
            models.Index(
                fields=["phone_number", "purpose", "date_time_created"],
                name="otp_phone_purpose_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.purpose}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expire_time

    @classmethod
    def delete_expired(cls):
        return cls.objects.filter(
            expire_time__lte=timezone.now()
        ).delete()
