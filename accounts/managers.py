
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .validator import validate_iranian_phone


class MyUserManager(BaseUserManager):
    def create_user(
        self,
        phone_number,
        full_name,
        password=None,
        **extra_fields,
    ):
        if not phone_number:
            raise ValueError(_("The phone number field is required."))

        if not full_name or not full_name.strip():
            raise ValueError(_("The full name field is required."))

        if not password:
            raise ValueError(_("Users must have a password."))

        phone_number = phone_number.strip()
        full_name = full_name.strip()

        try:
            validate_iranian_phone(phone_number)
        except ValidationError as exc:
            raise ValueError(_("Enter a valid phone number.")) from exc

        user = self.model(
            phone_number=phone_number,
            full_name=full_name,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        phone_number,
        full_name,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        if extra_fields.get("is_active") is not True:
            raise ValueError(_("Superuser must have is_active=True."))

        return self.create_user(
            phone_number=phone_number,
            full_name=full_name,
            password=password,
            **extra_fields,
        )
