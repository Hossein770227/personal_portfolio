import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


PHONE_REGEX = re.compile(r"^(?:\+98|0)9\d{9}$")


def validate_iranian_phone(value):
    if not PHONE_REGEX.fullmatch(value):
        raise ValidationError(
            _("Enter a valid Iranian mobile phone number.")
        )


def normalize_phone_number(phone):

    if phone.startswith("+98"):
        return "0" + phone[3:]
    return phone